// SPDX-License-Identifier: GPL-3.0-or-later
// Runtime selection + algebraic assembly tests ONLY. No solve()/time loop.
#include "argList.H"
#include "Time.H"
#include "fvMesh.H"
#include "volFields.H"
#include "fvMatrices.H"
#include "porosityModel.H"
#include "fvModel.H"
#include "IStringStream.H"
#include <cmath>
#include <iomanip>
#include <iostream>

using namespace Foam;
int main(int argc, char *argv[])
{
    argList::addOption("variant", "name", "normal or fail-stop input fixture");
    #include "setRootCase.H"
    #include "createTime.H"
    #include "createMesh.H"
    const word variant(args.optionLookupOrDefault<word>("variant", "normal"));
    const auto nuDim = sqr(dimLength)/dimTime;
    volVectorField U(IOobject("U", runTime.name(), mesh), mesh, dimensionedVector(dimVelocity, vector(2e-6,-3e-6,0)));
    volScalarField rho(IOobject("rho", runTime.name(), mesh), mesh, dimensionedScalar(dimDensity,1000));
    volScalarField mu(IOobject(variant=="noMu" ? "unusedMu" : "mu", runTime.name(), mesh), mesh, dimensionedScalar(dimDensity*nuDim,0.001));
    volScalarField nu(IOobject(variant=="noNu" ? "unusedNu" : "nu", runTime.name(), mesh), mesh, dimensionedScalar(nuDim,1e-6));
    volScalarField gap(IOobject("mesaGap", runTime.name(), mesh), mesh,
        dimensionedScalar(variant == "wrongGapUnits" ? dimless : dimLength,75e-9));
    int checks = 0;
    auto near = [&](scalar actual, scalar expected)
    {
        ++checks;
        if (!std::isfinite(actual) || mag(actual-expected) > 2e-11*max(mag(expected),scalar(1e-30)))
            FatalErrorInFunction << "Assembly mismatch actual=" << actual << " expected=" << expected << exit(FatalError);
    };
    for (int family=0; family<2; ++family)
    for (int angle : {0,90,45})
    for (int field=0; field<2; ++field)
    {
        const bool invalid = variant != "normal" && variant != "noMu" && variant != "noNu";
        if (invalid && (family != 0 || angle != 0 || field != 1)) continue;
        const std::string name = family ? "V2_published_rounded" : "original_local_cubic";
        const std::string e1 = angle==0 ? "(1 0 0)" : angle==90 ? "(0 1 0)" : "(1 1 0)";
        const std::string e2 = angle==0 ? "(0 1 0)" : angle==90 ? "(-1 0 0)" : "(-1 1 0)";
        const std::string settings =
            "type grooveDarcy; cellZone groove; grooveDarcyCoeffs { conductanceModel " + name
            + "; gapMode " + (field ? "field; gapField mesaGap;" : "uniform; mesaGap [0 1 0 0 0 0 0] 7.5e-8;")
            + " grooveDepth [0 1 0 0 0 0 0] 1e-7; grooveWidth [0 1 0 0 0 0 0] "
            + (variant=="unequalDuty" ? "1e-7;" : "1.2e-7;")
            + " period [0 1 0 0 0 0 0] 2.4e-7; velocityAverage fluidVolume; wallResistance totalUnresolved;"
            + (variant=="manualD" ? " d (1 1 0);" : "")
            + " coordinateSystem { type cartesian; origin (0 0 0); coordinateRotation { type axesRotation; e1 "
            + e1 + "; e2 " + e2 + "; } } }";
        IStringStream stream(settings);
        dictionary dict(stream);
        auto model = porosityModel::New("auditModel", mesh, dict);
        IStringStream wrapperStream("type porosityForce; porosityForceCoeffs {"+settings+"}");
        dictionary wrapperDict(wrapperStream);
        auto wrapper = fvModel::New("auditWrapper",mesh,wrapperDict);
        for (int update=0; update<(field ? 2 : 1); ++update)
        {
            forAll(gap, cell) gap[cell] = update ? (cell%2 ? 50e-9 : 100e-9) : 75e-9;
            if (variant=="zeroGap") gap[0]=0;
            if (variant=="negativeGap") gap[0]=-1e-9;
            if (variant=="nanGap") gap[0]=std::nan("");
            for (int massForm=0; massForm<2; ++massForm)
            {
                fvVectorMatrix eqn(U, variant=="wrongMatrixUnits" ? dimless : massForm ? dimForce/dimDensity : dimForce);
                volTensorField AU(IOobject("AU",runTime.name(),mesh),mesh,
                    dimensionedTensor(eqn.dimensions()/dimVolume/dimVelocity,Zero));
                model->addResistance(eqn);
                model->addResistance(eqn,AU,false);
                fvVectorMatrix sourceEqn(U,eqn.dimensions());
                if(massForm) wrapper->addSup(U,sourceEqn);
                else wrapper->addSup(rho,U,sourceEqn);
                const auto forces=model->force(U,rho,mu);
                const auto& cells=mesh.cellZones()["groove"];
                forAll(cells,i)
                {
                    const label cell=cells[i];
                    const scalar h=field ? gap[cell] : 75e-9;
                    // Separate analytic expressions, no production helper import.
                    const scalar H=h+50e-9, a=std::pow(h,3), b=std::pow(h+100e-9,3);
                    scalar kp=(a+b)/24, kt=1/(6*(1/a+1/b));
                    if(family) {kp/=1+1.7685*std::pow(5.0/6,1.6331); kt/=1+0.4900*std::pow(5.0/6,0.6990);}
                    const scalar dp=H/kp, dt=H/kt;
                    const scalar xx=angle==0 ? dp : angle==90 ? dt : (dp+dt)/2;
                    const scalar yy=angle==0 ? dt : angle==90 ? dp : (dp+dt)/2;
                    const scalar xy=angle==45 ? (dp-dt)/2 : 0;
                    const tensor D(xx,xy,0,xy,yy,0,0,0,0);
                    const vector expected=(massForm ? 1e-6 : 0.001)*mesh.V()[cell]*(D & U[cell]);
                    const vector actual=eqn.diag()[cell]*U[cell]-eqn.source()[cell];
                    for(int c=0;c<3;++c)
                    {
                        near(actual[c],expected[c]);
                        near(sourceEqn.diag()[cell]*U[cell][c]-sourceEqn.source()[cell][c],-expected[c]);
                        near(forces()[cell][c],0.001*mesh.V()[cell]*(D & U[cell])[c]);
                    }
                    for(int c=0;c<9;++c) near(AU[cell][c],(massForm ? 1e-6 : 0.001)*D[c]);
                    if(cell==cells[0] && !massForm)
                        std::cout<< std::setprecision(17)<<"COEFF "<<name<<" "<<angle<<" "<<field<<" "<<update<<" "<<h<<" "<<H<<" "<<kp<<" "<<kt<<" "<<AU[cell].xx()/0.001<<" "<<AU[cell].yy()/0.001<<"\n";
                }
                // Second half of the mesh is outside the porous zone.
                for(label cell=mesh.nCells()/2;cell<mesh.nCells();++cell)
                { near(eqn.diag()[cell],0); near(mag(eqn.source()[cell]),0); near(mag(AU[cell]),0); near(mag(forces()[cell]),0); }
            }
        }
    }
    if(variant!="normal" && variant!="noMu" && variant!="noNu") FatalErrorInFunction<<"Invalid fixture unexpectedly accepted"<<exit(FatalError);
    Info<<"ASSEMBLY_PASS scalar_checks="<<checks<<"; no flow solved"<<endl;
    return 0;
}
