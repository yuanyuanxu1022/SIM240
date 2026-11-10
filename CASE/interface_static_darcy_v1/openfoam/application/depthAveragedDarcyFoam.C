// SDI-v1: total Darcy resistance, physical pressure, one empty direction.
// D is read; K and the analytic pressure/velocity are never read or constructed.
#include "argList.H"
#include "Time.H"
#include "fvMesh.H"
#include "volFields.H"
#include "surfaceFields.H"
#include "fvmLaplacian.H"
#include "fvcGrad.H"
#include "fvcFlux.H"
#include "OSspecific.H"
#include <fstream>
#include <iostream>
#include <iomanip>
#include <cmath>
using namespace Foam;

int main(int argc,char* argv[])
{
    argList::noParallel();
    argList::addBoolOption("auditOnly", "Read input and mesh; do not assemble or solve pressure");
    #include "setRootCase.H"
    #include "createTime.H"
    #include "createMesh.H"

    IOdictionary props(IOobject("darcyProperties",runTime.constant(),mesh,IOobject::MUST_READ,IOobject::NO_WRITE));
    dimensionedScalar H(props.lookup("H")),mu(props.lookup("mu"));
    dimensionedScalar Dxx(props.lookup("Dxx")),Dyy(props.lookup("Dyy")),Dxy(props.lookup("Dxy"));
    if(H.dimensions()!=dimLength||mu.dimensions()!=dimensionSet(1,-1,-1,0,0,0,0)
       ||Dxx.dimensions()!=dimless/sqr(dimLength)||Dyy.dimensions()!=Dxx.dimensions()||Dxy.dimensions()!=Dxx.dimensions()
       ||!std::isfinite(H.value())||!std::isfinite(mu.value())||!std::isfinite(Dxx.value())||!std::isfinite(Dyy.value())||!std::isfinite(Dxy.value())
       ||H.value()<=0||mu.value()<=0||Dxx.value()<=0||Dyy.value()<=0||Dxy.value()!=0)
        FatalErrorInFunction<<"Invalid dimensions/positive diagonal SDI-v1 resistance"<<exit(FatalError);
    if(mesh.nCells()!=512||mesh.nGeometricD()!=2||mesh.nSolutionD()!=2)
        FatalErrorInFunction<<"C01 requires 512 cells and two solution dimensions"<<exit(FatalError);
    forAll(mesh.boundary(),patchi)
    {
        const word& name=mesh.boundary()[patchi].name();
        if(name!="xLow"&&name!="xHigh"&&name!="yLow"&&name!="yHigh"&&name!="frontAndBack")
            FatalErrorInFunction<<"Unexpected patch "<<name<<exit(FatalError);
        if((name=="frontAndBack")!=(mesh.boundary()[patchi].type()=="empty"))
            FatalErrorInFunction<<"Unexpected empty constraint"<<exit(FatalError);
    }
    if(mesh.boundary().size()!=5)FatalErrorInFunction<<"Expected five patches"<<exit(FatalError);
    volScalarField p(IOobject("p",runTime.name(),mesh,IOobject::MUST_READ,IOobject::AUTO_WRITE),mesh);
    if(p.dimensions()!=dimensionSet(1,-1,-2,0,0,0,0))FatalErrorInFunction<<"Pressure must be physical Pa"<<exit(FatalError);
    forAll(p.boundaryField(),patchi)
    {
        const word& name=mesh.boundary()[patchi].name();
        const word expected=name=="frontAndBack"?"empty":((name=="xLow"||name=="xHigh")?"fixedValue":"zeroGradient");
        if(p.boundaryField()[patchi].type()!=expected)FatalErrorInFunction<<"Unexpected p boundary for C01"<<exit(FatalError);
    }
    const scalar mx=1/(mu.value()*Dxx.value()),my=1/(mu.value()*Dyy.value());
    volTensorField M(IOobject("M",runTime.constant(),mesh,IOobject::NO_READ,IOobject::NO_WRITE),mesh,
        dimensionedTensor("mobility",dimensionSet(-1,3,1,0,0,0,0),tensor(mx,0,0,0,my,0,0,0,0)));
    // Assembly is audited without iterations; auditOnly never calls A.solve().
    fvScalarMatrix A(-fvm::laplacian(M,p));
    tmp<scalarField> diagonal=A.D();
    if(!A.symmetric()||gMin(diagonal())<=0||A.dimensions()!=dimVolume/dimTime)
        FatalErrorInFunction<<"Expected positive diagonal, symmetric volumetric-flux matrix"<<exit(FatalError);
    Info<<"SDI-v1: U=J/H, total resistance; no resolved wall shear, no extra fvModel"<<nl;
    if(args.optionFound("auditOnly"))
    {
        scalar maxInitialP=gMax(mag(p.primitiveField()));
        if(maxInitialP!=0)FatalErrorInFunction<<"Initial pressure must be zero"<<exit(FatalError);
        std::cout<<std::setprecision(17)<<"SDI_AUDIT {\"audit_only\":true,\"flow_solved\":false,\"cells\":"<<mesh.nCells()
            <<",\"volume_m3\":"<<gSum(mesh.V())<<",\"H_m\":"<<H.value()
            <<",\"Dxx_m_minus2\":"<<Dxx.value()<<",\"Dyy_m_minus2\":"<<Dyy.value()
            <<",\"initial_p_max_Pa\":"<<maxInitialP
            <<",\"matrix_assembled\":true,\"matrix_symmetric\":true,\"matrix_min_diagonal\":"<<gMin(diagonal())<<"}\n";
        return 0;
    }
    const fileName out=runTime.path()/"SDI_output";
    if(isDir(out))FatalErrorInFunction<<"Refusing existing output"<<exit(FatalError);
    mkDir(out);
    scalar initialRaw=0;
    {tmp<scalarField> r=A.residual();initialRaw=gSum(mag(r()));}
    SolverPerformance<scalar> performance=A.solve();
    p.correctBoundaryConditions();
    surfaceScalarField phi(IOobject("phi",runTime.name(),mesh,IOobject::NO_READ,IOobject::AUTO_WRITE),A.flux());
    volVectorField U(IOobject("U",runTime.name(),mesh,IOobject::NO_READ,IOobject::AUTO_WRITE),-(M & fvc::grad(p)));
    volVectorField J(IOobject("J",runTime.name(),mesh,IOobject::NO_READ,IOobject::AUTO_WRITE),H*U);
    surfaceScalarField phiU(IOobject("phi_U",runTime.name(),mesh,IOobject::NO_READ,IOobject::AUTO_WRITE),fvc::flux(U));
    scalar raw=0;{tmp<scalarField> r=A.residual();raw=gSum(mag(r()));}
    scalar trueNorm=raw/max(initialRaw,scalar(1e-300));
    bool finite=true;
    std::ofstream cells((out/"cells.csv").c_str());cells<<std::setprecision(17);
    cells<<"cell_id,x_m,y_m,z_m,volume_m3,p_Pa,Ux_m_s,Uy_m_s,Uz_m_s,Jx_m2_s,Jy_m2_s,Jz_m2_s\n";
    forAll(p,celli)
    {
        const vector& c=mesh.C()[celli];const vector& u=U[celli];const vector& j=J[celli];
        finite=finite&&std::isfinite(p[celli])&&std::isfinite(mag(u))&&std::isfinite(mag(j));
        cells<<celli<<','<<c.x()<<','<<c.y()<<','<<c.z()<<','<<mesh.V()[celli]<<','<<p[celli]<<','<<u.x()<<','<<u.y()<<','<<u.z()<<','<<j.x()<<','<<j.y()<<','<<j.z()<<'\n';
    }
    std::ofstream faces((out/"faces.csv").c_str());faces<<std::setprecision(17);
    faces<<"face_id,owner,neighbour,patch,x_m,y_m,z_m,Sx_m2,Sy_m2,Sz_m2,phi_m3_s,phi_U_m3_s\n";
    auto writeFace=[&](label facei,label owner,label neighbour,const word& patch,const vector& c,const vector& s,scalar q,scalar qu)
    {
        finite=finite&&std::isfinite(q)&&std::isfinite(qu);
        faces<<facei<<','<<owner<<','<<neighbour<<','<<patch<<','<<c.x()<<','<<c.y()<<','<<c.z()<<','<<s.x()<<','<<s.y()<<','<<s.z()<<','<<q<<','<<qu<<'\n';
    };
    forAll(mesh.neighbour(),facei)writeFace(facei,mesh.owner()[facei],mesh.neighbour()[facei],"internal",mesh.Cf()[facei],mesh.Sf()[facei],phi[facei],phiU[facei]);
    forAll(mesh.boundary(),patchi)
    {
        const fvPatch& patch=mesh.boundary()[patchi];if(patch.type()=="empty")continue;
        forAll(patch,locali)writeFace(patch.start()+locali,patch.faceCells()[locali],-1,patch.name(),mesh.Cf().boundaryField()[patchi][locali],mesh.Sf().boundaryField()[patchi][locali],phi.boundaryField()[patchi][locali],phiU.boundaryField()[patchi][locali]);
    }
    bool converged=finite&&performance.finalResidual()<=1e-12&&trueNorm<=1e-12&&performance.nIterations()<=2000;
    std::ofstream stats((out/"solver.json").c_str());stats<<std::setprecision(17)
       <<"{\"solver\":\"OpenFOAM13_PCG_DIC\",\"flow_solved\":true,\"converged\":"<<(converged?"true":"false")
       <<",\"iterations\":"<<performance.nIterations()<<",\"normalized_residual\":"<<performance.finalResidual()
       <<",\"initial_normalized_residual\":"<<performance.initialResidual()<<",\"true_normalized_residual\":"<<trueNorm
       <<",\"raw_residual_L1_m3_s\":"<<raw<<",\"normalization\":\"OpenFOAM_initial_normFactor_zero_initial_pressure\",\"cells\":"<<mesh.nCells()<<"}\n";
    cells.close();faces.close();stats.close();
    if(!cells||!faces||!stats)FatalErrorInFunction<<"CSV write failed"<<exit(FatalError);
    runTime.setTime(1,1);p.write();U.write();J.write();phi.write();phiU.write();
    Info<<"Flow solve completed; independent SDI result acceptance remains required"<<nl;
    return converged?0:2;
}
