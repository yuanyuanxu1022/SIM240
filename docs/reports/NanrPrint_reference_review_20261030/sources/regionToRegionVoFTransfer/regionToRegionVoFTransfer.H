/*---------------------------------------------------------------------------*\
  Class regionToRegionVoFTransfer Declarations
\*---------------------------------------------------------------------------*/

#ifndef regionToRegionVoFTransfer_H
#define regionToRegionVoFTransfer_H

#include "fvModel.H"
#include "compressibleVoF.H"
#include "mappedFvPatchBaseBase.H"

namespace Foam
{
namespace fv
{

/*---------------------------------------------------------------------------*\
        Class regionToRegionVoFSource Declaration
\*---------------------------------------------------------------------------*/

class regionToRegionVoFTarget;

class regionToRegionVoFSource
:
    public fvModel
{
    // Private Data
    const solvers::compressibleVoF& localVoF_;
    word localPatchName_;
    const label localPatchi_;
    word partnerRegionName_;
    word partnerPatchName_;
    word localPhaseName_;
    word partnerPhaseName_;

    //- Reference to the transferred phase thermo
    const rhoFluidThermo& thermo_;
    const volScalarField& localAlpha_;

    mutable label curTimeIndex_;
    
    scalar transferRateCoeff_;
    //- AlphaThreshold zone coefficients are per-time-step fractions that
    //  override transferRateCoeff directly. The region controls where
    //  cellZones are looked up: local or partner.
    word transferRateCoeffZoneRegion_;
    dictionary transferRateCoeffByZone_;
    scalar minLocalAlphaForTransfer_;
    scalar maxPartnerAlphaForTransfer_;
    scalar maxTransferFraction_;
    word transferModel_;
    word pressureFieldName_;
    word partnerPressureFieldName_;
    scalar pressureTransferCoeff_;
    scalar capillaryPressure_;
    word pressureTransferCoeffMaskFieldName_;
    word pressureTransferCoeffMaskRegion_;
    scalarList pressureTransferCoeffByMask_;
    bool requirePressureTransferCoeffMaskField_;
    word pressureTransferCoeffZoneRegion_;
    dictionary pressureTransferCoeffByZone_;
    dictionary pressureTransferResistanceByZone_;
    word alphaDependence_;
    scalar alphaReference_;
    word solidFractionFieldName_;
    word solidFractionRegion_;
    bool requireSolidFractionField_;


    volScalarField::Internal transferRate_;

    //- Return the transfer rate of field f
    template<class Type, class FieldType>
    inline tmp<Field<Type>> TransferRate(const FieldType& f) const;

    // Private Member Functions
    //- Find the partner Target model in the partner region
    const regionToRegionVoFTarget& partnerTarget(const fvMesh& mesh) const;

public:
    TypeName("regionToRegionVoFSource");

    // Constructors
    regionToRegionVoFSource
    (
        const word& sourceName,
        const word& modelType,
        const fvMesh& mesh,
        const dictionary& dict
    );

    virtual ~regionToRegionVoFSource() = default;


    
    // Member Functions

    const volScalarField& alpha() const
    {
        return localAlpha_;
    }

    virtual wordList addSupFields() const;

    virtual void correct();

    virtual void addSup
    (
        const volScalarField& alpha,
        const volScalarField& rho,
        fvMatrix<scalar>& eqn
    ) const;

    virtual void addSup
    (
        const volScalarField& alpha,
        const volScalarField& rho,
        const volScalarField& he,
        fvMatrix<scalar>& eqn
    ) const;

    virtual void addSup
    (
        const volScalarField& rho,
        const volVectorField& U,
        fvMatrix<vector>& eqn
    ) const;

    // Transfer to Target
    //- Return the mass transfer rate
    tmp<scalarField> rhoTransferRate() const;

    //- Return the energy transfer rate
    tmp<scalarField> heTransferRate() const;

    //- Return the momentum transfer rate
    tmp<vectorField> UTransferRate() const;

    // Mesh changes
    virtual void topoChange(const polyTopoChangeMap&);
    virtual void mapMesh(const polyMeshMap&);
    virtual void distribute(const polyDistributionMap&);
    virtual bool movePoints();
};


/*---------------------------------------------------------------------------*\
        Class regionToRegionVoFTarget Declaration
\*---------------------------------------------------------------------------*/

class regionToRegionVoFTarget
:
    public fvModel
{
    // Private Data
    const solvers::compressibleVoF& localVoF_;
    word localPatchName_;
    const label localPatchi_;
    word partnerRegionName_;
    word partnerPatchName_;
    word localPhaseName_;
    word partnerPhaseName_;

    //- Reference to the transferred phase thermo
    const rhoFluidThermo& thermo_;
    const volScalarField& localAlpha_;


    mutable label curTimeIndex_;
    scalar transferRateCoeff_;

    // Cached transfer rate from Source
    mutable volScalarField::Internal targetTransferRate_;

    // Private Member Functions
    //- Find the partner Source model in the partner region
    const regionToRegionVoFSource& partnerSource(const fvMesh& mesh) const;

    //- Return the transfer rate from the Source
    template<class Type, class TransferRateFunc>
    inline tmp<VolInternalField<Type>> sourceTransferRate
    (
        TransferRateFunc transferRateFunc,
        const dimensionSet& dimProp
    ) const;

public:
    TypeName("regionToRegionVoFTarget");

    // Constructors
    regionToRegionVoFTarget
    (
        const word& sourceName,
        const word& modelType,
        const fvMesh& mesh,
        const dictionary& dict
    );

    virtual ~regionToRegionVoFTarget() = default;

    // Member Functions
    virtual wordList addSupFields() const;

    virtual void correct();

    virtual void addSup
    (
        const volScalarField& alpha,
        const volScalarField& rho,
        fvMatrix<scalar>& eqn
    ) const;

    virtual void addSup
    (
        const volScalarField& alpha,
        const volScalarField& rho,
        const volScalarField& he,
        fvMatrix<scalar>& eqn
    ) const;

    virtual void addSup
    (
        const volScalarField& rho,
        const volVectorField& U,
        fvMatrix<vector>& eqn
    ) const;

    // Mesh changes
    virtual void topoChange(const polyTopoChangeMap&);
    virtual void mapMesh(const polyMeshMap&);
    virtual void distribute(const polyDistributionMap&);
    virtual bool movePoints();
};

} // End namespace fv
} // End namespace Foam

#endif