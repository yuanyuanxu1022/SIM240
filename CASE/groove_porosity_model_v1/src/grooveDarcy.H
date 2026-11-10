// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef grooveDarcy_H
#define grooveDarcy_H
#include "porosityModel.H"
#include "volFields.H"

namespace Foam { namespace porosityModels {
// Total unresolved wall drag, fluid-volume mean velocity, xy empty domain only.
class grooveDarcy : public porosityModel
{
    word model_, gapMode_, gapFieldName_, rhoName_, muName_, nuName_;
    scalar gap_, depth_, width_, period_;
    tensor parallelProjector_, transverseProjector_;
    tensorField resistance() const;
    tmp<scalarField> viscosity(const fvVectorMatrix&) const;
    void apply(fvVectorMatrix&, const scalarField&, const tensorField&) const;

public:
    TypeName("grooveDarcy");
    grooveDarcy(const word&, const fvMesh&, const dictionary&, const dictionary&, const word&);
    virtual ~grooveDarcy() = default;
    void calcTransformModelData() override;
    void calcForce(const volVectorField&, const volScalarField&, const volScalarField&, vectorField&) const override;
    void correct(fvVectorMatrix&) const override;
    void correct(const fvVectorMatrix&, volTensorField&) const override;
    bool read(const dictionary&) override;
    grooveDarcy(const grooveDarcy&) = delete;
    void operator=(const grooveDarcy&) = delete;
};
}}
#endif
