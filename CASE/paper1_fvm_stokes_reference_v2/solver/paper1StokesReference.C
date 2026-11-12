/* OpenFOAM Foundation 13; GPL-3.0-or-later.
 * Steady, constant-viscosity, no-slip periodic reference ONLY.
 * P: scalar -nu Laplacian(v) = a; physical velocity is (0,v,0).
 * T: -nu Laplacian(U) + grad(p) = a*ex; div(U)=0.
 * p is kinematic periodic pressure. There is NO transient or advection term.
 * Pressure correction follows the Foundation icoFoam pressure equation, with
 * its transient/advection contributions omitted for this steady Stokes model.
 * Compilation and meshing do not qualify a numerical reference.
 */
#include "argList.H"
#include "simpleControl.H"
#include "findRefCell.H"
#include "constrainPressure.H"
#include "constrainHbyA.H"
#include "adjustPhi.H"
#include "fvmLaplacian.H"
#include "fvcGrad.H"
#include "fvcDiv.H"
#include "fvcFlux.H"
#include "fvcVolumeIntegrate.H"
#include "OFstream.H"
#include "OSspecific.H"

using namespace Foam;

// One row per complete fluid cell; no height normalization in this export.
void writeCells
(
    const fvMesh& mesh, const vectorField& velocity,
    const scalarField& gradNorm2, const scalarField& strainDissPerMass,
    const scalarField& pressure
)
{
    const fileName output(mesh.time().path()/"referenceEvidence");
    mkDir(output);
    OFstream cells(output/"cells.csv");
    cells.precision(17);
    cells << "x_m,y_m,z_m,V_m3,Ux_m_s,Uy_m_s,Uz_m_s,grad_norm2_s2,diss_per_mass_m2_s3,p_kin_m2_s2\n";
    forAll(mesh.V(), c)
    {
        const vector& x = mesh.C()[c];
        const vector& u = velocity[c];
        cells << x.x() << ',' << x.y() << ',' << x.z() << ','
            << mesh.V()[c] << ',' << u.x() << ',' << u.y() << ','
            << u.z() << ',' << gradNorm2[c] << ','
            << strainDissPerMass[c] << ',' << pressure[c] << '\n';
    }
}

// For transverse continuity: all x-normal faces, including both cyclic ends.
// Orient every flux towards +x, then group by x in the offline reader.
void writeSections(const fvMesh& mesh, const surfaceScalarField& phi)
{
    OFstream faces(mesh.time().path()/"referenceEvidence"/"x_faces.csv");
    faces.precision(17);
    faces << "x_m,flux_positive_x_m3_s,area_m2\n";
    const vectorField& fc = mesh.faceCentres();
    const vectorField& sf = mesh.faceAreas();
    forAll(fc, f)
    {
        if (mag(sf[f].x()) < 0.999999*mag(sf[f])) continue;
        scalar q = 0;
        if (f < mesh.nInternalFaces()) q = phi[f];
        else
        {
            const label patch = mesh.boundaryMesh().whichPatch(f);
            q = phi.boundaryField()[patch][f-mesh.boundaryMesh()[patch].start()];
        }
        faces << fc[f].x() << ',' << (sf[f].x() > 0 ? q : -q)
            << ',' << mag(sf[f]) << '\n';
    }
}

int main(int argc, char *argv[])
{
    #include "setRootCase.H"
    #include "createTime.H"
    #include "createMesh.H"
    if (Pstream::parRun())
    {
        FatalErrorInFunction << "Serial reference only: MPI is not prepared."
            << exit(FatalError);
    }
    IOdictionary properties
    (
        IOobject("referenceProperties", runTime.constant(), mesh,
            IOobject::MUST_READ, IOobject::NO_WRITE)
    );
    const word direction(properties.lookup("direction"));
    dimensionedScalar nu("nu", dimKinematicViscosity, properties.lookup("nu"));
    dimensionedScalar acceleration("acceleration", dimAcceleration,
        properties.lookup("acceleration"));
    simpleControl simple(mesh);
    if (direction == "P")
    {
        volScalarField v
        (
            IOobject("v", runTime.name(), mesh, IOobject::MUST_READ,
                IOobject::AUTO_WRITE), mesh
        );
        while (simple.loop(runTime))
        {
            while (simple.correctNonOrthogonal())
            {
                fvScalarMatrix equation(-fvm::laplacian(nu, v) == acceleration);
                equation.solve();
            }
            runTime.write();
        }
        runTime.writeNow();
        const volVectorField gradient(fvc::grad(v));
        vectorField velocity(mesh.nCells(), vector::zero);
        scalarField gradient2(mesh.nCells(), 0), diss(mesh.nCells(), 0);
        forAll(velocity, c)
        {
            velocity[c].y() = v[c];
            gradient2[c] = magSqr(gradient[c]);
            diss[c] = nu.value()*gradient2[c];
        }
        writeCells(mesh, velocity, gradient2, diss,
            scalarField(mesh.nCells(), 0));
        Info<< "REFERENCE_EQUATION scalar_Poisson_no_inertia\n";
    }
    else if (direction == "T")
    {
        volVectorField U
        (
            IOobject("U", runTime.name(), mesh, IOobject::MUST_READ,
                IOobject::AUTO_WRITE), mesh
        );
        volScalarField p
        (
            IOobject("p", runTime.name(), mesh, IOobject::MUST_READ,
                IOobject::AUTO_WRITE), mesh
        );
        surfaceScalarField phi
        (
            IOobject("phi", runTime.name(), mesh, IOobject::READ_IF_PRESENT,
                IOobject::AUTO_WRITE), fvc::flux(U)
        );
        label pRefCell = 0;
        scalar pRefValue = 0;
        setRefCell(p, simple.dict(), pRefCell, pRefValue);
        mesh.schemes().setFluxRequired(p.name());
        const dimensionedVector force("force", dimAcceleration,
            vector(acceleration.value(), 0, 0));
        while (simple.loop(runTime))
        {
            // The source is assembled into UEqn, so UEqn.H includes it.
            fvVectorMatrix UEqn(-fvm::laplacian(nu, U) == force);
            UEqn.relax();
            solve(UEqn == -fvc::grad(p));
            volScalarField rAU(1.0/UEqn.A());
            volVectorField HbyA(constrainHbyA(rAU*UEqn.H(), U, p));
            surfaceScalarField phiHbyA("phiHbyA", fvc::flux(HbyA));
            adjustPhi(phiHbyA, U, p);
            constrainPressure(p, U, phiHbyA, rAU);
            while (simple.correctNonOrthogonal())
            {
                fvScalarMatrix pEqn
                (
                    fvm::laplacian(rAU, p) == fvc::div(phiHbyA)
                );
                pEqn.setReference(pRefCell, pRefValue);
                pEqn.solve();
                if (simple.finalNonOrthogonalIter())
                    phi = phiHbyA - pEqn.flux();
            }
            p.relax();
            U = HbyA - rAU*fvc::grad(p);
            U.correctBoundaryConditions();
            runTime.write();
        }
        runTime.writeNow();
        const volTensorField gradient(fvc::grad(U));
        scalarField gradient2(mesh.nCells(), 0), diss(mesh.nCells(), 0);
        forAll(gradient2, c)
        {
            gradient2[c] = magSqr(gradient[c]);
            diss[c] = 2*nu.value()*magSqr(symm(gradient[c]));
        }
        writeCells(mesh, U.primitiveField(), gradient2, diss, p.primitiveField());
        writeSections(mesh, phi);
        Info<< "REFERENCE_EQUATION vector_Stokes_no_inertia\n";
    }
    else
    {
        FatalErrorInFunction << "direction must be P or T" << exit(FatalError);
    }
    Info<< "Reference evidence exported; this is NOT acceptance.\nEnd\n";
    return 0;
}
