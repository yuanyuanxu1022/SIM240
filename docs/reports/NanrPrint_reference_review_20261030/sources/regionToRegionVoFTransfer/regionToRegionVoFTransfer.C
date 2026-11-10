/*---------------------------------------------------------------------------*\
  Implementation of regionToRegionVoFTransfer
\*---------------------------------------------------------------------------*/

#include "regionToRegionVoFTransfer.H"
#include "fvmSup.H"
#include "addToRunTimeSelectionTable.H"
#include "mappedFvPatchBaseBase.H"

// * * * * * * * * * * * * * Static Data Members * * * * * * * * * * * * //

namespace Foam
{
namespace fv
{
    defineTypeNameAndDebug(regionToRegionVoFSource, 0);
    addToRunTimeSelectionTable(fvModel, regionToRegionVoFSource, dictionary);

    defineTypeNameAndDebug(regionToRegionVoFTarget, 0);
    addToRunTimeSelectionTable(fvModel, regionToRegionVoFTarget, dictionary);
}
}



using namespace Foam;

// ************************************************************************* //
//                  regionToRegionVoFSource Implementation
// ************************************************************************* //

fv::regionToRegionVoFSource::regionToRegionVoFSource
(
    const word& sourceName,
    const word& modelType,
    const fvMesh& mesh,
    const dictionary& dict
)
:
    fvModel(sourceName, modelType, mesh, dict),
    localVoF_(mesh.lookupObject<solvers::compressibleVoF>(solver::typeName)),
    localPatchName_(dict.lookup("localPatch")),
    localPatchi_(mesh.boundaryMesh().findIndex(localPatchName_)),
    partnerRegionName_(dict.lookup("partnerRegion")),
    partnerPatchName_(dict.lookup("partnerPatch")),
    localPhaseName_(dict.lookup("localPhase")),
    partnerPhaseName_(dict.lookup("partnerPhase")),
    thermo_
    (
        localPhaseName_ == localVoF_.mixture.phase1Name()
      ? localVoF_.mixture.thermo1()
      : localVoF_.mixture.thermo2()
    ),
    localAlpha_
    (
        localPhaseName_ == localVoF_.mixture.phase1Name()
      ? localVoF_.mixture.alpha1()
      : localVoF_.mixture.alpha2()
    ),
    curTimeIndex_(-1),
    transferRateCoeff_(dict.lookupOrDefault<scalar>("transferRateCoeff", 0.1)),
    transferRateCoeffZoneRegion_
    (
        dict.lookupOrDefault<word>("transferRateCoeffZoneRegion", "partner")
    ),
    transferRateCoeffByZone_
    (
        dict.subOrEmptyDict("transferRateCoeffByZone")
    ),
    minLocalAlphaForTransfer_(dict.lookupOrDefault<scalar>("minLocalAlphaForTransfer", 0.99)),
    maxPartnerAlphaForTransfer_(dict.lookupOrDefault<scalar>("maxPartnerAlphaForTransfer", 0.99)),
    maxTransferFraction_(dict.lookupOrDefault<scalar>("maxTransferFraction", 0.2)),
    transferModel_(dict.lookupOrDefault<word>("transferModel", "alphaThreshold")),
    pressureFieldName_(dict.lookupOrDefault<word>("pressureField", "p")),
    partnerPressureFieldName_(dict.lookupOrDefault<word>("partnerPressureField", pressureFieldName_)),
    pressureTransferCoeff_(dict.lookupOrDefault<scalar>("pressureTransferCoeff", 0)),
    capillaryPressure_(dict.lookupOrDefault<scalar>("capillaryPressure", 0)),
    pressureTransferCoeffMaskFieldName_(dict.lookupOrDefault<word>("pressureTransferCoeffMaskField", "")),
    pressureTransferCoeffMaskRegion_(dict.lookupOrDefault<word>("pressureTransferCoeffMaskRegion", "partner")),
    pressureTransferCoeffByMask_(dict.lookupOrDefault<scalarList>("pressureTransferCoeffByMask", scalarList())),
    requirePressureTransferCoeffMaskField_(dict.lookupOrDefault<bool>("requirePressureTransferCoeffMaskField", false)),
    pressureTransferCoeffZoneRegion_(dict.lookupOrDefault<word>("pressureTransferCoeffZoneRegion", "partner")),
    pressureTransferCoeffByZone_(dict.subOrEmptyDict("pressureTransferCoeffByZone")),
    pressureTransferResistanceByZone_(dict.subOrEmptyDict("pressureTransferResistanceByZone")),
    alphaDependence_(dict.lookupOrDefault<word>("alphaDependence", "none")),
    alphaReference_(dict.lookupOrDefault<scalar>("alphaReference", 1)),
    solidFractionFieldName_(dict.lookupOrDefault<word>("solidFractionField", "solidFraction")),
    solidFractionRegion_(dict.lookupOrDefault<word>("solidFractionRegion", "partner")),
    requireSolidFractionField_(dict.lookupOrDefault<bool>("requireSolidFractionField", false)),
    transferRate_
    (
        volScalarField::Internal::New
        (
            "transferRate",
            mesh,
            dimensionedScalar(dimless/dimTime, 0)
        )
    )
{
    if (!isA<mappedFvPatchBaseBase>(mesh.boundary()[localPatchi_]))
    {
        FatalErrorInFunction
            << "The patch " << localPatchName_ << " must be of type 'mapped'."
            << exit(FatalError);
    }

    if (pressureTransferCoeffMaskRegion_ != "local"
     && pressureTransferCoeffMaskRegion_ != "partner")
    {
        FatalErrorInFunction
            << "pressureTransferCoeffMaskRegion must be local or partner."
            << exit(FatalError);
    }

    if (transferRateCoeffZoneRegion_ != "local"
     && transferRateCoeffZoneRegion_ != "partner")
    {
        FatalErrorInFunction
            << "transferRateCoeffZoneRegion must be local or partner."
            << exit(FatalError);
    }

    if (pressureTransferCoeffZoneRegion_ != "local"
     && pressureTransferCoeffZoneRegion_ != "partner")
    {
        FatalErrorInFunction
            << "pressureTransferCoeffZoneRegion must be local or partner."
            << exit(FatalError);
    }

    if (solidFractionRegion_ != "local"
     && solidFractionRegion_ != "partner")
    {
        FatalErrorInFunction
            << "solidFractionRegion must be local or partner."
            << exit(FatalError);
    }

    if (alphaDependence_ != "none" && alphaDependence_ != "linear")
    {
        FatalErrorInFunction
            << "alphaDependence must be none or linear."
            << exit(FatalError);
    }

    if (alphaReference_ <= small)
    {
        FatalErrorInFunction
            << "alphaReference must be positive."
            << exit(FatalError);
    }
}

wordList fv::regionToRegionVoFSource::addSupFields() const
{
    const word rhoName("rho."+localPhaseName_);
    return wordList{rhoName, thermo_.he().name(), localVoF_.U.name()};
}

const Foam::fv::regionToRegionVoFTarget& Foam::fv::regionToRegionVoFSource::partnerTarget(const fvMesh& mesh) const
{
    const fvModels& models = fvModels::New(mesh);
    const regionToRegionVoFTarget* targetPtr = nullptr;

    forAll(models, i)
    {
        if (isType<regionToRegionVoFTarget>(models[i]))
        {
            const regionToRegionVoFTarget& target = refCast<const regionToRegionVoFTarget>(models[i]);
            targetPtr = &target;
        }
    }

    if (!targetPtr)
    {
        FatalErrorInFunction
            << "Cannot find regionToRegionVoFTarget model in region " << mesh.name()
            << exit(FatalError);
    }

    return *targetPtr;
}

void fv::regionToRegionVoFSource::correct()
{
    if (curTimeIndex_ == mesh().time().timeIndex())
    {
        return;
    }
    curTimeIndex_ = mesh().time().timeIndex();

    const scalar deltaT = mesh().time().deltaTValue();
    const fvPatch& locPatch = mesh().boundary()[localPatchi_];
    const mappedFvPatchBaseBase& mapper = refCast<const mappedFvPatchBaseBase>(locPatch);

    const fvMesh& partnerMesh = mapper.nbrMesh();
    const solvers::compressibleVoF& partnerSolver =
        partnerMesh.lookupObject<solvers::compressibleVoF>(solver::typeName);
    const volScalarField& partnerAlpha =
        (partnerPhaseName_ == partnerSolver.mixture.phase1Name()
         ? partnerSolver.mixture.alpha1()
         : partnerSolver.mixture.alpha2());

    const scalarField partnerAlphaMapped = mapper.fromNeighbour(partnerAlpha);
    const scalarField& localAlphaFace = localAlpha_.boundaryField()[localPatchi_];
    const labelList& faceCells = locPatch.faceCells();

    transferRate_ = Zero;

    scalarField maxPartnerAlphaFace(faceCells.size(), maxPartnerAlphaForTransfer_);

    if (!solidFractionFieldName_.empty())
    {
        scalarField solidFractionFace(faceCells.size(), 0);
        bool foundSolidFractionField = false;

        if (solidFractionRegion_ == "partner")
        {
            if (partnerMesh.foundObject<volScalarField>(solidFractionFieldName_))
            {
                const volScalarField& solidFraction =
                    partnerMesh.lookupObject<volScalarField>(solidFractionFieldName_);
                solidFractionFace = mapper.fromNeighbour(solidFraction);
                foundSolidFractionField = true;
            }
            else
            {
                typeIOobject<volScalarField> solidFractionHeader
                (
                    solidFractionFieldName_,
                    partnerMesh.time().name(),
                    partnerMesh,
                    IOobject::READ_IF_PRESENT,
                    IOobject::NO_WRITE,
                    false
                );

                if (solidFractionHeader.headerOk())
                {
                    const volScalarField solidFraction(solidFractionHeader, partnerMesh);
                    solidFractionFace = mapper.fromNeighbour(solidFraction);
                    foundSolidFractionField = true;
                }

                if (!foundSolidFractionField)
                {
                    typeIOobject<volScalarField> solidFractionZeroHeader
                    (
                        solidFractionFieldName_,
                        "0",
                        partnerMesh,
                        IOobject::READ_IF_PRESENT,
                        IOobject::NO_WRITE,
                        false
                    );

                    if (solidFractionZeroHeader.headerOk())
                    {
                        const volScalarField solidFraction(solidFractionZeroHeader, partnerMesh);
                        solidFractionFace = mapper.fromNeighbour(solidFraction);
                        foundSolidFractionField = true;
                    }
                }
            }
        }
        else
        {
            if (mesh().foundObject<volScalarField>(solidFractionFieldName_))
            {
                const volScalarField& solidFraction =
                    mesh().lookupObject<volScalarField>(solidFractionFieldName_);
                solidFractionFace = solidFraction.boundaryField()[localPatchi_];
                foundSolidFractionField = true;
            }
            else
            {
                typeIOobject<volScalarField> solidFractionHeader
                (
                    solidFractionFieldName_,
                    mesh().time().name(),
                    mesh(),
                    IOobject::READ_IF_PRESENT,
                    IOobject::NO_WRITE,
                    false
                );

                if (solidFractionHeader.headerOk())
                {
                    const volScalarField solidFraction(solidFractionHeader, mesh());
                    solidFractionFace = solidFraction.boundaryField()[localPatchi_];
                    foundSolidFractionField = true;
                }

                if (!foundSolidFractionField)
                {
                    typeIOobject<volScalarField> solidFractionZeroHeader
                    (
                        solidFractionFieldName_,
                        "0",
                        mesh(),
                        IOobject::READ_IF_PRESENT,
                        IOobject::NO_WRITE,
                        false
                    );

                    if (solidFractionZeroHeader.headerOk())
                    {
                        const volScalarField solidFraction(solidFractionZeroHeader, mesh());
                        solidFractionFace = solidFraction.boundaryField()[localPatchi_];
                        foundSolidFractionField = true;
                    }
                }
            }
        }

        if (foundSolidFractionField)
        {
            forAll(faceCells, i)
            {
                const scalar porosity =
                    max(scalar(0), scalar(1) - min(max(solidFractionFace[i], scalar(0)), scalar(1)));
                maxPartnerAlphaFace[i] = min(maxPartnerAlphaFace[i], porosity);
            }
        }
        else if (requireSolidFractionField_)
        {
            FatalErrorInFunction
                << "Cannot find solidFraction field " << solidFractionFieldName_
                << " in " << solidFractionRegion_ << " region"
                << exit(FatalError);
        }
    }

    if (transferModel_ == "alphaThreshold")
    {
        scalarField transferCoeffFace(faceCells.size(), transferRateCoeff_);

        // transferRateCoeffByZone values are dimensionless per-time-step
        // transfer fractions. They override transferRateCoeff directly, are
        // not multiplied by it, and transferRateCoeffZoneRegion controls
        // where the cellZones are looked up.
        if (transferRateCoeffByZone_.size())
        {
            const fvMesh& zoneMesh =
                transferRateCoeffZoneRegion_ == "partner" ? partnerMesh : mesh();

            volScalarField zoneCoeff
            (
                IOobject
                (
                    "transferRateCoeffByZoneField",
                    zoneMesh.time().name(),
                    zoneMesh,
                    IOobject::NO_READ,
                    IOobject::NO_WRITE,
                    false
                ),
                zoneMesh,
                dimensionedScalar(dimless, transferRateCoeff_)
            );

            scalarField& zoneCoeffCells = zoneCoeff.primitiveFieldRef();

            const wordList zoneNames = transferRateCoeffByZone_.toc();

            forAll(zoneNames, zoneNamei)
            {
                const word& zoneName = zoneNames[zoneNamei];
                const label zonei = zoneMesh.cellZones().findIndex(zoneName);

                if (zonei < 0)
                {
                    FatalErrorInFunction
                        << "Cannot find transferRateCoeffByZone cellZone "
                        << zoneName << " in region " << zoneMesh.name()
                        << exit(FatalError);
                }

                const scalar coeff =
                    transferRateCoeffByZone_.lookup<scalar>(zoneName);
                const labelList& zoneCells = zoneMesh.cellZones()[zonei];

                forAll(zoneCells, i)
                {
                    zoneCoeffCells[zoneCells[i]] = coeff;
                }
            }

            zoneCoeff.correctBoundaryConditions();

            if (transferRateCoeffZoneRegion_ == "partner")
            {
                transferCoeffFace = mapper.fromNeighbour(zoneCoeff);
            }
            else
            {
                transferCoeffFace = zoneCoeff.boundaryField()[localPatchi_];
            }
        }

        forAll(faceCells, i)
        {
            const label celli = faceCells[i];

            const bool localIsReady =
                localAlphaFace[i] >= minLocalAlphaForTransfer_;

            const scalar remainingPartnerCapacity =
                max(maxPartnerAlphaFace[i] - partnerAlphaMapped[i], scalar(0));

            const bool partnerHasCapacity =
                remainingPartnerCapacity > small;

            if (localIsReady && partnerHasCapacity)
            {
                transferRate_[celli] =
                    min
                    (
                        min(transferCoeffFace[i], maxTransferFraction_),
                        remainingPartnerCapacity
                    )/deltaT;
            }
        }
    }
    else if (transferModel_ == "pressureDriven")
    {
        const volScalarField* localPPtr = nullptr;
        const volScalarField* partnerPPtr = nullptr;

        if (mesh().foundObject<volScalarField>(pressureFieldName_))
        {
            localPPtr = &mesh().lookupObject<volScalarField>(pressureFieldName_);
        }
        if (partnerMesh.foundObject<volScalarField>(partnerPressureFieldName_))
        {
            partnerPPtr = &partnerMesh.lookupObject<volScalarField>(partnerPressureFieldName_);
        }

        if (!localPPtr && pressureFieldName_ != "p_rgh"
         && mesh().foundObject<volScalarField>("p_rgh"))
        {
            localPPtr = &mesh().lookupObject<volScalarField>("p_rgh");
        }
        if (!partnerPPtr && partnerPressureFieldName_ != "p_rgh"
         && partnerMesh.foundObject<volScalarField>("p_rgh"))
        {
            partnerPPtr = &partnerMesh.lookupObject<volScalarField>("p_rgh");
        }

        if (!localPPtr || !partnerPPtr)
        {
            FatalErrorInFunction
                << "pressureDriven transfer requires pressure fields. Local field: "
                << pressureFieldName_ << ", partner field: " << partnerPressureFieldName_
                << exit(FatalError);
        }

        const volScalarField& localP = *localPPtr;
        const volScalarField& partnerP = *partnerPPtr;
        const scalarField& localPFace = localP.boundaryField()[localPatchi_];
        const scalarField partnerPMapped = mapper.fromNeighbour(partnerP);
        const scalar maxRate = maxTransferFraction_/deltaT;
        scalarField pressureTransferCoeffFace(faceCells.size(), pressureTransferCoeff_);

        if (pressureTransferCoeffByMask_.size())
        {
            if (pressureTransferCoeffMaskFieldName_.empty())
            {
                FatalErrorInFunction
                    << "pressureTransferCoeffByMask requires "
                    << "pressureTransferCoeffMaskField."
                    << exit(FatalError);
            }

            scalarField maskFace(faceCells.size(), 0);

            if (pressureTransferCoeffMaskRegion_ == "partner")
            {
                if (partnerMesh.foundObject<volScalarField>(pressureTransferCoeffMaskFieldName_))
                {
                    const volScalarField& mask =
                        partnerMesh.lookupObject<volScalarField>
                        (
                            pressureTransferCoeffMaskFieldName_
                        );
                    maskFace = mapper.fromNeighbour(mask);
                }
                else
                {
                    typeIOobject<volScalarField> maskHeader
                    (
                        pressureTransferCoeffMaskFieldName_,
                        partnerMesh.time().name(),
                        partnerMesh,
                        IOobject::READ_IF_PRESENT,
                        IOobject::NO_WRITE,
                        false
                    );

                    if (maskHeader.headerOk())
                    {
                        const volScalarField mask(maskHeader, partnerMesh);
                        maskFace = mapper.fromNeighbour(mask);
                    }
                    else if (requirePressureTransferCoeffMaskField_)
                    {
                        FatalErrorInFunction
                            << "Cannot find mask field "
                            << pressureTransferCoeffMaskFieldName_
                            << " in partner region " << partnerMesh.name()
                            << exit(FatalError);
                    }
                }
            }
            else
            {
                if (mesh().foundObject<volScalarField>(pressureTransferCoeffMaskFieldName_))
                {
                    const volScalarField& mask =
                        mesh().lookupObject<volScalarField>
                        (
                            pressureTransferCoeffMaskFieldName_
                        );
                    maskFace = mask.boundaryField()[localPatchi_];
                }
                else
                {
                    typeIOobject<volScalarField> maskHeader
                    (
                        pressureTransferCoeffMaskFieldName_,
                        mesh().time().name(),
                        mesh(),
                        IOobject::READ_IF_PRESENT,
                        IOobject::NO_WRITE,
                        false
                    );

                    if (maskHeader.headerOk())
                    {
                        const volScalarField mask(maskHeader, mesh());
                        maskFace = mask.boundaryField()[localPatchi_];
                    }
                    else if (requirePressureTransferCoeffMaskField_)
                    {
                        FatalErrorInFunction
                            << "Cannot find mask field "
                            << pressureTransferCoeffMaskFieldName_
                            << " in local region " << mesh().name()
                            << exit(FatalError);
                    }
                }
            }

            forAll(faceCells, i)
            {
                const label maski = round(maskFace[i]);

                if (maski >= 0 && maski < pressureTransferCoeffByMask_.size())
                {
                    pressureTransferCoeffFace[i] = pressureTransferCoeffByMask_[maski];
                }
            }
        }

        if (pressureTransferCoeffByZone_.size()
         || pressureTransferResistanceByZone_.size())
        {
            const fvMesh& zoneMesh =
                pressureTransferCoeffZoneRegion_ == "partner" ? partnerMesh : mesh();

            volScalarField zoneCoeff
            (
                IOobject
                (
                    "pressureTransferCoeffByZoneField",
                    zoneMesh.time().name(),
                    zoneMesh,
                    IOobject::NO_READ,
                    IOobject::NO_WRITE,
                    false
                ),
                zoneMesh,
                dimensionedScalar(dimless, pressureTransferCoeff_)
            );

            scalarField& zoneCoeffCells = zoneCoeff.primitiveFieldRef();

            const wordList coeffZoneNames = pressureTransferCoeffByZone_.toc();
            forAll(coeffZoneNames, zoneNamei)
            {
                const word& zoneName = coeffZoneNames[zoneNamei];
                const label zonei = zoneMesh.cellZones().findIndex(zoneName);

                if (zonei < 0)
                {
                    FatalErrorInFunction
                        << "Cannot find pressureTransferCoeffByZone cellZone "
                        << zoneName << " in region " << zoneMesh.name()
                        << exit(FatalError);
                }

                const scalar coeff =
                    pressureTransferCoeffByZone_.lookup<scalar>(zoneName);
                const labelList& zoneCells = zoneMesh.cellZones()[zonei];

                forAll(zoneCells, i)
                {
                    zoneCoeffCells[zoneCells[i]] = coeff;
                }
            }

            const wordList resistanceZoneNames = pressureTransferResistanceByZone_.toc();
            forAll(resistanceZoneNames, zoneNamei)
            {
                const word& zoneName = resistanceZoneNames[zoneNamei];
                const label zonei = zoneMesh.cellZones().findIndex(zoneName);

                if (zonei < 0)
                {
                    FatalErrorInFunction
                        << "Cannot find pressureTransferResistanceByZone cellZone "
                        << zoneName << " in region " << zoneMesh.name()
                        << exit(FatalError);
                }

                const scalar resistance =
                    pressureTransferResistanceByZone_.lookup<scalar>(zoneName);

                if (resistance <= small)
                {
                    FatalErrorInFunction
                        << "pressureTransferResistanceByZone for " << zoneName
                        << " must be positive."
                        << exit(FatalError);
                }

                const scalar coeff = 1.0/resistance;
                const labelList& zoneCells = zoneMesh.cellZones()[zonei];

                forAll(zoneCells, i)
                {
                    zoneCoeffCells[zoneCells[i]] = coeff;
                }
            }

            zoneCoeff.correctBoundaryConditions();

            if (pressureTransferCoeffZoneRegion_ == "partner")
            {
                pressureTransferCoeffFace = mapper.fromNeighbour(zoneCoeff);
            }
            else
            {
                pressureTransferCoeffFace = zoneCoeff.boundaryField()[localPatchi_];
            }
        }

        forAll(faceCells, i)
        {
            const label celli = faceCells[i];
            const bool localIsReady = (localAlphaFace[i] >= minLocalAlphaForTransfer_);
            const scalar remainingPartnerCapacity =
                max(maxPartnerAlphaFace[i] - partnerAlphaMapped[i], scalar(0));
            const bool partnerHasCapacity = (remainingPartnerCapacity > small);
            const scalar faceMaxRate = min(maxRate, remainingPartnerCapacity/deltaT);
            const scalar drivingPressure =
                localPFace[i] - partnerPMapped[i] - capillaryPressure_;

            scalar alphaFactor = 1;
            if (alphaDependence_ == "linear")
            {
                alphaFactor = min(max(localAlphaFace[i]/alphaReference_, scalar(0)), scalar(1));
            }

            if (localIsReady && partnerHasCapacity && drivingPressure > 0)
            {
                transferRate_[celli] =
                    min
                    (
                        alphaFactor*pressureTransferCoeffFace[i]*drivingPressure,
                        faceMaxRate
                    );
            }
        }
    }
    else
    {
        FatalErrorInFunction
            << "Unknown transferModel '" << transferModel_
            << "'. Valid options are alphaThreshold and pressureDriven."
            << exit(FatalError);
    }
}

void fv::regionToRegionVoFSource::addSup
(
    const volScalarField& alpha,
    const volScalarField& rho,
    fvMatrix<scalar>& eqn
) const
{
    if (&alpha != &localAlpha_) return;

    // Remove mass implicitly
    // S = -K * rho * alpha => Sp = -K * rho

    // Potentially implicit transfer out of the VoF
    if (&rho == &eqn.psi())
    {
        eqn -= fvm::Sp(alpha()*transferRate_, eqn.psi());
    }
    else if (&alpha == &eqn.psi())
    {
        eqn -= fvm::Sp(rho()*transferRate_, eqn.psi());
    }
    else
    {
        eqn -= alpha()*rho()*transferRate_;
    }
    
}

void fv::regionToRegionVoFSource::addSup
(
    const volScalarField& alpha,
    const volScalarField& rho,
    const volScalarField& he,
    fvMatrix<scalar>& eqn
) const
{
    if (&alpha != &localAlpha_) return;

    // Potentially implicit transfer out of the VoF
    if (&he == &eqn.psi())
    {
        eqn -= fvm::Sp(alpha()*rho()*transferRate_, eqn.psi());
    }
    else
    {
        eqn -= alpha()*rho()*he*transferRate_;
    }
}

void fv::regionToRegionVoFSource::addSup
(
    const volScalarField& rho,
    const volVectorField& U,
    fvMatrix<vector>& eqn
) const
{
    if (&U != &localVoF_.U) return;

    // Potentially implicit transfer out of the VoF
    if (&U == &eqn.psi())
    {
        eqn -= fvm::Sp(alpha()*rho()*transferRate_, eqn.psi());
    }
    else
    {
        eqn -= alpha()*rho()*U*transferRate_;
    }
}


template<class Type, class FieldType>
inline Foam::tmp<Foam::Field<Type>> Foam::fv::regionToRegionVoFSource::TransferRate
(
    const FieldType& f
) const
{
    const fvPatch& locPatch = mesh().boundary()[localPatchi_];

    const labelList& faceCells = locPatch.faceCells();


    return tmp<Field<Type>>
    (
        new Field<Type>
        (
            UIndirectList<Type>
            (
                alpha()*transferRate_*mesh().V()*f,
                faceCells
            )
        )
    );
}


Foam::tmp<Foam::scalarField>
Foam::fv::regionToRegionVoFSource::rhoTransferRate() const
{
    return TransferRate<scalar>(thermo_.rho()());
}


Foam::tmp<Foam::scalarField>
Foam::fv::regionToRegionVoFSource::heTransferRate() const
{
    return TransferRate<scalar>(thermo_.rho()()*thermo_.he()());
}


Foam::tmp<Foam::vectorField>
Foam::fv::regionToRegionVoFSource::UTransferRate() const
{
    return TransferRate<vector>(thermo_.rho()()*localVoF_.U());
}



void fv::regionToRegionVoFSource::topoChange(const polyTopoChangeMap& map)
{
    transferRate_.setSize(mesh().nCells());
}

void fv::regionToRegionVoFSource::mapMesh(const polyMeshMap& map)
{
    transferRate_.setSize(mesh().nCells());
}

void fv::regionToRegionVoFSource::distribute(const polyDistributionMap& map)
{
    transferRate_.setSize(mesh().nCells());
}

bool fv::regionToRegionVoFSource::movePoints()
{
    return true;
}

// ************************************************************************* //
//                  regionToRegionVoFTarget Implementation
// ************************************************************************* //

fv::regionToRegionVoFTarget::regionToRegionVoFTarget
(
    const word& sourceName,
    const word& modelType,
    const fvMesh& mesh,
    const dictionary& dict
)
:
    fvModel(sourceName, modelType, mesh, dict),
    localVoF_(mesh.lookupObject<solvers::compressibleVoF>(solver::typeName)),
    localPatchName_(dict.lookup("localPatch")),
    localPatchi_(mesh.boundaryMesh().findIndex(localPatchName_)),
    partnerRegionName_(dict.lookup("partnerRegion")),
    partnerPatchName_(dict.lookup("partnerPatch")),
    localPhaseName_(dict.lookup("localPhase")),
    partnerPhaseName_(dict.lookup("partnerPhase")),
    thermo_
    (
        localPhaseName_ == localVoF_.mixture.phase1Name()
      ? localVoF_.mixture.thermo1()
      : localVoF_.mixture.thermo2()
    ),
    localAlpha_
    (
        localPhaseName_ == localVoF_.mixture.phase1Name()
      ? localVoF_.mixture.alpha1()
      : localVoF_.mixture.alpha2()
    ),
    curTimeIndex_(-1),
    transferRateCoeff_(dict.lookupOrDefault<scalar>("transferRateCoeff", 0.1)),
    targetTransferRate_
    (
        volScalarField::Internal::New
        (
            "targetTransferRate",
            mesh,
            dimensionedScalar(dimMass/dimTime, 0)
        )
    )
{
    if (!isA<mappedFvPatchBaseBase>(mesh.boundary()[localPatchi_]))
    {
        FatalErrorInFunction
            << "The patch " << localPatchName_ << " must be of type 'mapped'."
            << exit(FatalError);
    }
}

wordList fv::regionToRegionVoFTarget::addSupFields() const
{
    const word rhoName("rho."+localPhaseName_);
    return wordList{rhoName, thermo_.he().name(), localVoF_.U.name()};
}

const Foam::fv::regionToRegionVoFSource& Foam::fv::regionToRegionVoFTarget::partnerSource(const fvMesh& mesh) const
{
    const fvModels& models = fvModels::New(mesh);
    const regionToRegionVoFSource* sourcePtr = nullptr;

    forAll(models, i)
    {
        if (isType<regionToRegionVoFSource>(models[i]))
        {
            const regionToRegionVoFSource& source = refCast<const regionToRegionVoFSource>(models[i]);

            sourcePtr = &source;

        }
    }

    if (!sourcePtr)
    {
        FatalErrorInFunction
            << "Cannot find regionToRegionVoFSource model in region " << mesh.name()
            << exit(FatalError);
    }

    return *sourcePtr;
}

template<class Type, class TransferRateFunc>
Foam::tmp<Foam::VolInternalField<Type>>
Foam::fv::regionToRegionVoFTarget::sourceTransferRate
(
    TransferRateFunc transferRateFunc,
    const dimensionSet& dimProp
) const
{
    const fvPatch& locPatch = mesh().boundary()[localPatchi_];
    const mappedFvPatchBaseBase& mapper = refCast<const mappedFvPatchBaseBase>(locPatch);

    // Get the Source model from the partner region
    const regionToRegionVoFSource& source = partnerSource(mapper.nbrMesh());

    // Create temporary field for source
    tmp<VolInternalField<Type>> tSu
    (
        VolInternalField<Type>::New
        (
            "Su",
            mesh(),
            dimensioned<Type>(dimProp/dimTime, Zero)
        )
    );

    // Map the Source's transfer rate to this mesh
    UIndirectList<Type>(tSu.ref(), locPatch.faceCells()) =
        mapper.fromNeighbour((source.*transferRateFunc)());

    // Convert from [property/s] to [property/m3/s] for fvMatrix
    return tSu / mesh().V();
}

void fv::regionToRegionVoFTarget::correct()
{
    if (curTimeIndex_ == mesh().time().timeIndex())
    {
        return;
    }
    curTimeIndex_ = mesh().time().timeIndex();

    targetTransferRate_ = Zero;
}

void fv::regionToRegionVoFTarget::addSup
(
    const volScalarField& alpha,
    const volScalarField& rho,
    fvMatrix<scalar>& eqn
) const
{
    if (&alpha != &localAlpha_) return;

    // Explicit addition of mass
    // Target receives the mass flow rate calculated by Source
    eqn += sourceTransferRate<scalar>
    (
        &regionToRegionVoFSource::rhoTransferRate,
        dimMass
    );

}

void fv::regionToRegionVoFTarget::addSup
(
    const volScalarField& alpha,
    const volScalarField& rho,
    const volScalarField& he,
    fvMatrix<scalar>& eqn
) const
{
    if (&alpha != &localAlpha_) return;


    // Simple approach: Use the explicit source term
    eqn += sourceTransferRate<scalar>
    (
        &regionToRegionVoFSource::heTransferRate,
        dimEnergy
    ); 
}

void fv::regionToRegionVoFTarget::addSup
(
    const volScalarField& rho,
    const volVectorField& U,
    fvMatrix<vector>& eqn
) const
{
    if (&U != &localVoF_.U) return;

    eqn += sourceTransferRate<vector>
    (
        &regionToRegionVoFSource::UTransferRate,
        dimMomentum
    ) ; 
}

void fv::regionToRegionVoFTarget::topoChange(const polyTopoChangeMap& map)
{
    targetTransferRate_.setSize(mesh().nCells());
}

void fv::regionToRegionVoFTarget::mapMesh(const polyMeshMap& map)
{
    targetTransferRate_.setSize(mesh().nCells());
}

void fv::regionToRegionVoFTarget::distribute(const polyDistributionMap& map)
{
    targetTransferRate_.setSize(mesh().nCells());
}

bool fv::regionToRegionVoFTarget::movePoints()
{
    return true;
}