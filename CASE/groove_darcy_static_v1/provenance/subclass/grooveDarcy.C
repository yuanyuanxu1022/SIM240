// SPDX-License-Identifier: GPL-3.0-or-later
// Matrix splitting follows Foundation 13 DarcyForchheimer (2012-2024,
// OpenFOAM Foundation, GPL-3.0-or-later). Geometry closure is SIM240-specific.
#include "grooveDarcy.H"
#include "grooveTransport.H"
#include "addToRunTimeSelectionTable.H"
#include "fvMatrices.H"

namespace Foam { namespace porosityModels {
defineTypeNameAndDebug(grooveDarcy, 0);
addToRunTimeSelectionTable(porosityModel, grooveDarcy, mesh);

grooveDarcy::grooveDarcy
(
    const word& name, const fvMesh& mesh, const dictionary& dict,
    const dictionary& c, const word& zone
)
:
    porosityModel(name, mesh, dict, c, zone),
    model_(c.lookup<word>("conductanceModel")),
    gapMode_(c.lookup<word>("gapMode")),
    gapFieldName_(c.lookupOrDefault<word>("gapField", "mesaGap")),
    rhoName_(c.lookupOrDefault<word>("rho", "rho")),
    muName_(c.lookupOrDefault<word>("mu", "mu")),
    nuName_(c.lookupOrDefault<word>("nu", "nu")),
    gap_(gapMode_ == "uniform" ? dimensionedScalar("mesaGap", dimLength, c).value() : 1e-7),
    depth_(dimensionedScalar("grooveDepth", dimLength, c).value()),
    width_(dimensionedScalar("grooveWidth", dimLength, c).value()),
    period_(dimensionedScalar("period", dimLength, c).value()),
    parallelProjector_(Zero), transverseProjector_(Zero)
{
    if ((model_ != "original_local_cubic" && model_ != "V2_published_rounded")
     || (gapMode_ != "uniform" && gapMode_ != "field")
     || c.lookup<word>("velocityAverage") != "fluidVolume"
     || c.lookup<word>("wallResistance") != "totalUnresolved")
        FatalIOErrorInFunction(c) << "Unsupported model/average/wall/gap convention" << exit(FatalIOError);
    if (c.found("d") || c.found("f") || c.found("H")
     || (gapMode_ == "field" && c.found("mesaGap"))
     || (gapMode_ == "uniform" && c.found("gapField")))
        FatalIOErrorInFunction(c) << "Do not supply d/f/H or conflicting gap inputs; coefficients are computed" << exit(FatalIOError);
    try { sim240::transport(gap_, depth_, width_, period_, model_ == "V2_published_rounded"); }
    catch (const std::exception& e)
    { FatalIOErrorInFunction(c) << e.what() << exit(FatalIOError); }
    calcTransformModelData();
    Info<< "grooveDarcy: " << model_ << ", gapMode=" << gapMode_
        << ", H=mesaGap+(grooveWidth/period)*grooveDepth, D=H/K; xy total drag only" << nl;
}

void grooveDarcy::calcTransformModelData()
{
    if (mesh_.nGeometricD() != 2 || mesh_.geometricD().z() != -1
     || !coordSys_.R().uniform())
        FatalErrorInFunction << "Require xy 2D empty mesh and uniform coordinate rotation; 3D closure undefined" << exit(FatalError);
    parallelProjector_ = coordSys_.R().transform(Zero, tensor(1,0,0,0,0,0,0,0,0));
    transverseProjector_ = coordSys_.R().transform(Zero, tensor(0,0,0,0,1,0,0,0,0));
    const tensor plane = parallelProjector_ + transverseProjector_;
    if (mag(plane-tensor(1,0,0,0,1,0,0,0,0)) > 1e-10)
        FatalErrorInFunction << "Local x (along) and y (across) must span the global xy plane" << exit(FatalError);
}

tensorField grooveDarcy::resistance() const
{
    const labelList& cells = mesh_.cellZones()[zoneName_];
    const volScalarField* h = nullptr;
    if (gapMode_ == "field")
    {
        h = &mesh_.lookupObject<volScalarField>(gapFieldName_);
        if (h->dimensions() != dimLength)
            FatalErrorInFunction << "gapField must have length dimensions" << exit(FatalError);
    }
    tensorField D(cells.size(), Zero);
    forAll(cells, i)
    {
        try
        {
            const auto r = sim240::transport(h ? (*h)[cells[i]] : gap_, depth_, width_, period_, model_ == "V2_published_rounded");
            D[i] = r.Dparallel*parallelProjector_ + r.Dperpendicular*transverseProjector_;
        }
        catch (const std::exception& e)
        { FatalErrorInFunction << "cell " << cells[i] << ": " << e.what() << exit(FatalError); }
    }
    return D; // Recompute on every assembly: also catches updates within one time step.
}

tmp<scalarField> grooveDarcy::viscosity(const fvVectorMatrix& eqn) const
{
    const auto& U = eqn.psi();
    auto lookup = [&](const word& name, const dimensionSet& dims) -> const volScalarField&
    {
        const auto& f = mesh_.lookupObject<volScalarField>(IOobject::groupName(name, U.group()));
        if (f.dimensions() != dims)
            FatalErrorInFunction << "Wrong dimensions for " << f.name() << exit(FatalError);
        return f;
    };
    tmp<scalarField> result(new scalarField(U.size(), 0));
    const auto muDims = dimDensity*(sqr(dimLength)/dimTime);
    if (eqn.dimensions() == dimForce)
    {
        if (mesh_.foundObject<volScalarField>(IOobject::groupName(muName_, U.group())))
            result.ref() = lookup(muName_, muDims).primitiveField();
        else
            result.ref() = lookup(rhoName_, dimDensity).primitiveField()*lookup(nuName_, (sqr(dimLength)/dimTime)).primitiveField();
    }
    else if (eqn.dimensions() == dimForce/dimDensity)
    {
        if (mesh_.foundObject<volScalarField>(IOobject::groupName(nuName_, U.group())))
            result.ref() = lookup(nuName_, (sqr(dimLength)/dimTime)).primitiveField();
        else
            result.ref() = lookup(muName_, muDims).primitiveField()/lookup(rhoName_, dimDensity).primitiveField();
    }
    else FatalErrorInFunction << "Unsupported momentum matrix dimensions " << eqn.dimensions() << exit(FatalError);
    for (label cell : mesh_.cellZones()[zoneName_])
        if (!std::isfinite(result()[cell]) || result()[cell] <= 0)
            FatalErrorInFunction << "Nonpositive/nonfinite viscosity at cell " << cell << exit(FatalError);
    return result;
}

void grooveDarcy::apply(fvVectorMatrix& eqn, const scalarField& visc, const tensorField& D) const
{
    const labelList& cells = mesh_.cellZones()[zoneName_];
    forAll(cells, i)
    {
        const label cell = cells[i];
        const tensor Cd = visc[cell]*D[i];
        const scalar iso = tr(Cd);
        eqn.diag()[cell] += mesh_.V()[cell]*iso;
        eqn.source()[cell] -= mesh_.V()[cell]*((Cd-I*iso) & eqn.psi()[cell]);
    }
}

void grooveDarcy::correct(fvVectorMatrix& eqn) const
{
    const tensorField D(resistance());
    const auto visc = viscosity(eqn);
    apply(eqn, visc(), D);
}

void grooveDarcy::correct(const fvVectorMatrix& eqn, volTensorField& AU) const
{
    if (AU.dimensions() != eqn.dimensions()/dimVolume/dimVelocity)
        FatalErrorInFunction << "Incorrect AU dimensions" << exit(FatalError);
    const tensorField D(resistance());
    const auto visc = viscosity(eqn);
    const labelList& cells = mesh_.cellZones()[zoneName_];
    forAll(cells, i) AU[cells[i]] += visc()[cells[i]]*D[i];
}

void grooveDarcy::calcForce(const volVectorField& U, const volScalarField&, const volScalarField& mu, vectorField& force) const
{
    if (U.dimensions() != dimVelocity || mu.dimensions() != dimDensity*(sqr(dimLength)/dimTime))
        FatalErrorInFunction << "force() requires velocity and dynamic viscosity" << exit(FatalError);
    force = Zero;
    const tensorField D(resistance());
    const labelList& cells = mesh_.cellZones()[zoneName_];
    forAll(cells, i)
    {
        const label cell = cells[i];
        if (!std::isfinite(mu[cell]) || mu[cell] <= 0)
            FatalErrorInFunction << "Invalid dynamic viscosity" << exit(FatalError);
        // Positive resistance on matrix LHS; physical fluid source is its negative.
        force[cell] = mesh_.V()[cell]*mu[cell]*(D[i] & U[cell]);
    }
}

bool grooveDarcy::read(const dictionary&)
{
    FatalErrorInFunction << "Dictionary hot reload unsupported: reconstruct model. Registered gapField may be updated in place." << exit(FatalError);
    return false;
}
}}
