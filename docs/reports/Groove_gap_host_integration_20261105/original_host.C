// SPDX-License-Identifier: GPL-3.0-or-later
// GDI-v1. Native porosityForce momentum assembly, physical pressure.
// No transport formula, direct D input, transient, convection or viscous term.
#include "argList.H"
#include "Time.H"
#include "fvMesh.H"
#include "volFields.H"
#include "surfaceFields.H"
#include "fvMatrices.H"
#include "fvmLaplacian.H"
#include "fvcGrad.H"
#include "fvcDiv.H"
#include "fvcFlux.H"
#include "porosityForce.H"
#include "porosityModel.H"
#include "constrainHbyA.H"
#include "OSspecific.H"
#include <fstream>
#include <iomanip>
#include <cmath>
using namespace Foam;

static void require(bool ok, const char* message)
{ if (!ok) FatalErrorInFunction<<message<<exit(FatalError); }
static bool gdiFinite(scalar x) {return std::isfinite(x);}
static void checkStream(const std::ofstream& f) {require(bool(f),"Output write failed");}

int main(int argc,char* argv[])
{
    argList::noParallel();
    argList::addBoolOption("auditOnly","Assemble and export audit evidence; never solve");
    argList::addBoolOption("solve","Explicitly solve the sealed GDI01 case");
    argList::addOption("runId","id","GDI01_v1_ prefixed run identity for solve mode");
    #include "setRootCase.H"
    #include "createTime.H"
    #include "createMesh.H"
    const bool audit=args.optionFound("auditOnly");
    require(audit != args.optionFound("solve"),"Choose exactly one of -auditOnly or -solve; no default solve");
    const word runId=args.optionLookupOrDefault<word>("runId","AUDIT_ONLY_NO_FLOW_RUN");
    require(audit || runId.find("GDI01_v1_")==0,"Solve mode needs a GDI01_v1_ run identity");
    require(mesh.nCells()==512 && mesh.nGeometricD()==2 && mesh.nSolutionD()==2,"Require 512-cell xy empty mesh");
    require(mesh.cellZones().size()==1,"Exactly one porous cellZone required");
    const labelList& zone=mesh.cellZones()["groove"];
    boolList seen(mesh.nCells(),false);
    require(zone.size()==mesh.nCells(),"Porous zone must cover every cell");
    for (label cell : zone) {require(cell>=0 && cell<mesh.nCells() && !seen[cell],"Missing/duplicate zone cell");seen[cell]=true;}

    IOdictionary settings(IOobject("gdiProperties",runTime.constant(),mesh,IOobject::MUST_READ,IOobject::NO_WRITE));
    IOdictionary models(IOobject("fvModels",runTime.constant(),mesh,IOobject::MUST_READ,IOobject::NO_WRITE));
    require(models.size()==1 && models.found("grooveResistance"),"Exactly one porosityForce source required");
    const dictionary& md=models.subDict("grooveResistance");
    require(md.lookup<word>("type")=="porosityForce","Not a standard porosityForce wrapper");
    const dictionary& mc=md.subDict("porosityForceCoeffs");
    require(mc.lookup<word>("type")=="grooveDarcy" && mc.lookup<word>("cellZone")=="groove","Wrong native model/zone");
    const dictionary& c=mc.subDict("grooveDarcyCoeffs");
    require(c.lookup<word>("conductanceModel")=="V2_published_rounded" && c.lookup<word>("gapMode")=="uniform","GDI01 requires uniform V2");
    const scalar gap=dimensionedScalar("mesaGap",dimLength,c).value();
    const scalar depth=dimensionedScalar("grooveDepth",dimLength,c).value();
    const scalar width=dimensionedScalar("grooveWidth",dimLength,c).value();
    const scalar period=dimensionedScalar("period",dimLength,c).value();
    const dimensionedScalar H("H",dimLength,gap+width/period*depth);
    require(gap==75e-9 && depth==100e-9 && width==120e-9 && period==240e-9,"Wrong GDI01 geometry inputs");
    const dimensionedScalar mu0("mu",dimensionSet(1,-1,-1,0,0,0,0),settings);
    const dimensionedScalar rho0("rho",dimDensity,settings);
    const dimensionedScalar nu0("nu",sqr(dimLength)/dimTime,settings);
    const dimensionedScalar scaleU("velocityScale",dimVelocity,settings);
    require(mu0.value()==0.001 && rho0.value()==1000 && nu0.value()==1e-6 && mag(mu0.value()/(rho0.value()*nu0.value())-1)<1e-12,"Wrong viscosity/density");
    require(gdiFinite(scaleU.value()) && scaleU.value()>0,"Invalid normalization velocity");
    const scalar lx=24e-6,ly=48e-6,dp=24,G=dp/lx,Qs=scaleU.value()*H.value()*ly;
    require(mag(H.value()/125e-9-1)<1e-12 && mag(gSum(mesh.V())/(lx*ly*H.value())-1)<1e-10,"Wrong mesh volume/mean thickness");
    forAll(mesh.C(),i)
    {
        const vector q=mesh.C()[i];
        const scalar ix=q.x()/(lx/16)-0.5,iy=q.y()/(ly/32)-0.5;
        require(mag(ix-std::round(ix))<1e-10 && mag(iy-std::round(iy))<1e-10
            && ix>-1e-10 && ix<15+1e-10 && iy>-1e-10 && iy<31+1e-10
            && mag(q.z()/H.value()-0.5)<1e-10
            && mag(mesh.V()[i]/(lx*ly*H.value()/512)-1)<1e-10,"Wrong cell geometry");
    }
    volScalarField p(IOobject("p",runTime.name(),mesh,IOobject::MUST_READ,IOobject::AUTO_WRITE),mesh);
    volVectorField U(IOobject("U",runTime.name(),mesh,IOobject::MUST_READ,IOobject::AUTO_WRITE),mesh);
    require(p.dimensions()==dimensionSet(1,-1,-2,0,0,0,0) && U.dimensions()==dimVelocity,"p must be Pa, U must be m/s");
    require(gMax(mag(p.primitiveField()))==0 && gMax(mag(U.primitiveField()))==0,"Internal initial p and U must be zero");
    require(mesh.boundary().size()==5,"Five named patches required");
    forAll(mesh.boundary(),pi)
    {
        const word name=mesh.boundary()[pi].name();
        const bool end=name=="xLow" || name=="xHigh",side=name=="yLow" || name=="yHigh",z=name=="frontAndBack";
        require(end || side || z,"Unknown patch");
        require((mesh.boundary()[pi].type()=="empty")==z,"Wrong mesh empty boundary");
        require(p.boundaryField()[pi].type()==(z ? "empty" : end ? "fixedValue" : "zeroGradient"),"Wrong p boundary type");
        require(U.boundaryField()[pi].type()==(z ? "empty" : end ? "zeroGradient" : "slip"),"Wrong U boundary type");
        if(end) for(scalar val:p.boundaryField()[pi]) require(val==(name=="xLow" ? 24 : 0),"Wrong physical boundary pressure");
    }
    const dictionary& linear=mesh.solution().solverDict("p");
    require(linear.lookup<word>("solver")=="PCG" && linear.lookup<word>("preconditioner")=="DIC"
        && linear.lookup<scalar>("tolerance")==1e-12 && linear.lookup<scalar>("relTol")==0
        && linear.lookup<label>("maxIter")==2000,"Frozen linear solver settings changed");
    p.correctBoundaryConditions();U.correctBoundaryConditions();
    volScalarField rho(IOobject("rho",runTime.name(),mesh),mesh,rho0);
    volScalarField mu(IOobject("mu",runTime.name(),mesh),mesh,mu0);
    volScalarField nu(IOobject("nu",runTime.name(),mesh),mesh,nu0);
    autoPtr<fvModel> wrapper=fvModel::New("grooveResistance",mesh,md);
    require(isA<fv::porosityForce>(wrapper()),"Wrapper runtime type mismatch");
    const porosityModel& model=refCast<const fv::porosityForce>(wrapper()).model();
    require(model.type()=="grooveDarcy" && model.zoneName()=="groove","Submodel runtime type mismatch");
    require(wrapper->addsSupToField("U"),"porosityForce is not assigned to U");

    // Obtain D from model force responses, not from input D or a K formula.
    tensorField D(mesh.nCells(),Zero);
    volVectorField probe(IOobject("coefficientProbe",runTime.name(),mesh),mesh,dimensionedVector(dimVelocity,Zero));
    for(label a=0;a<3;++a)
    {
        vector basis(Zero);basis[a]=1;probe.primitiveFieldRef()=basis;
        const tmp<vectorField> response=model.force(probe,rho,mu);
        forAll(D,i) for(label k=0;k<3;++k) D[i](k,a)=response()[i][k]/(mu0.value()*mesh.V()[i]);
    }
    for(const tensor& d:D)
        require(gdiFinite(d.xx()) && gdiFinite(d.yy()) && d.xx()>d.yy() && d.yy()>0
            && mag(d.xy())/d.xx()<1e-12 && mag(d.yx())/d.xx()<1e-12
            && mag(d.zz())==0,"Wrong GDI01 cross-groove tensor response");

    const fileName out=runTime.path()/(audit ? "GDI_audit" : "GDI_output");
    require(!isDir(out),"Refusing to overwrite output directory");mkDir(out);
    std::ofstream coefficients((out/"coefficients.csv").c_str());coefficients<<std::setprecision(17);
    coefficients<<"cell_id,H_m,Dxx_m_minus2,Dxy_m_minus2,Dxz_m_minus2,Dyx_m_minus2,Dyy_m_minus2,Dyz_m_minus2,Dzx_m_minus2,Dzy_m_minus2,Dzz_m_minus2,zone_member\n";
    forAll(D,i){coefficients<<i<<','<<H.value();for(label k=0;k<9;++k) coefficients<<','<<D[i][k];coefficients<<",1\n";}checkStream(coefficients);coefficients.close();
    auto writeFieldsCSV=[&](const surfaceScalarField& phi,const surfaceScalarField& phiU)
    {
        std::ofstream cells((out/"cells.csv").c_str());cells<<std::setprecision(17);
        cells<<"cell_id,x_m,y_m,z_m,volume_m3,p_Pa,Ux_m_s,Uy_m_s,Uz_m_s,Jx_m2_s,Jy_m2_s,Jz_m2_s\n";
        forAll(p,i){const vector x=mesh.C()[i],u=U[i],j=H.value()*u;cells<<i<<','<<x.x()<<','<<x.y()<<','<<x.z()<<','<<mesh.V()[i]<<','<<p[i]<<','<<u.x()<<','<<u.y()<<','<<u.z()<<','<<j.x()<<','<<j.y()<<','<<j.z()<<'\n';}checkStream(cells);
        std::ofstream faces((out/"faces.csv").c_str());faces<<std::setprecision(17);
        faces<<"face_id,owner,neighbour,patch,x_m,y_m,z_m,Sx_m2,Sy_m2,Sz_m2,phi_m3_s,phi_U_m3_s\n";
        auto face=[&](label fi,label own,label nei,const word& patch,const vector& x,const vector& s,scalar q,scalar qu)
        {faces<<fi<<','<<own<<','<<nei<<','<<patch<<','<<x.x()<<','<<x.y()<<','<<x.z()<<','<<s.x()<<','<<s.y()<<','<<s.z()<<','<<q<<','<<qu<<'\n';};
        forAll(mesh.neighbour(),fi) face(fi,mesh.owner()[fi],mesh.neighbour()[fi],"internal",mesh.Cf()[fi],mesh.Sf()[fi],phi[fi],phiU[fi]);
        forAll(mesh.boundary(),pi){const fvPatch& patch=mesh.boundary()[pi];if(patch.type()=="empty")continue;forAll(patch,li)face(patch.start()+li,patch.faceCells()[li],-1,patch.name(),mesh.Cf().boundaryField()[pi][li],mesh.Sf().boundaryField()[pi][li],phi.boundaryField()[pi][li],phiU.boundaryField()[pi][li]);}checkStream(faces);
    };
    std::ofstream history;
    if(!audit){history.open((out/"iteration_history.csv").c_str());history<<std::setprecision(17);history<<"outer,linear_iterations,normalized_residual,initial_raw_L1_m3_s,final_raw_L1_m3_s,true_normalized_residual,momentum_L2_relative,momentum_max_relative,delta_U_L2_relative,delta_U_max_relative,delta_p_max_relative,global_mass_relative,local_mass_relative,side_leakage_relative,face_flux_consistency_relative,energy_relative\n";}
    bool converged=false;label lastOuter=0,lastLinear=0;scalar lastNorm=GREAT,lastTrue=GREAT,lastRaw=GREAT;
    for(label outer=1;outer<=(audit ? 1 : 2000);++outer)
    {
        const vectorField oldU(U.primitiveField());const scalarField oldP(p.primitiveField());
        fvVectorMatrix momentum(-wrapper->source(rho,U));
        require(momentum.dimensions()==dimForce && gMin(momentum.diag())>0,"Expected positive physical momentum matrix");
        volScalarField rAU(1.0/momentum.A());
        volVectorField HbyA(constrainHbyA(rAU*momentum.H(),U,p));
        HbyA.correctBoundaryConditions();
        surfaceScalarField phiHat("phiHbyA",fvc::flux(HbyA));
        p.primitiveFieldRef()=0;p.correctBoundaryConditions();
        // Multiply the specified pressure equation by -1 for SPD assembly.
        // Consequently canonical pressure flux = -pressure.flux().
        fvScalarMatrix pressure(-fvm::laplacian(rAU,p)==-fvc::div(phiHat));
        require(pressure.dimensions()==dimVolume/dimTime && pressure.symmetric() && gMin(pressure.D()())>0,"Invalid pressure matrix");
        if(audit)
        {
            std::ofstream matrix((out/"matrix.csv").c_str());matrix<<std::setprecision(17);
            matrix<<"cell_id,momentum_diag_kg_s,momentum_source_x_N,momentum_source_y_N,momentum_source_z_N,pressure_diagonal,pressure_source,rAU\n";
            const scalarField diag(pressure.D());
            forAll(p,i){matrix<<i<<','<<momentum.diag()[i]<<','<<momentum.source()[i].x()<<','<<momentum.source()[i].y()<<','<<momentum.source()[i].z()<<','<<diag[i]<<','<<pressure.source()[i]<<','<<rAU[i]<<'\n';}checkStream(matrix);matrix.close();
            surfaceScalarField zeroPhi("zeroPhi",fvc::flux(U));writeFieldsCSV(zeroPhi,zeroPhi);
            std::ofstream auditFile((out/"audit.json").c_str());auditFile<<std::setprecision(17)
                <<"{\"protocol_id\":\"GDI-v1\",\"case_id\":\"GDI01\",\"audit_only\":true,\"flow_solved\":false,\"solve_calls\":0,\"cells\":"<<mesh.nCells()<<",\"zone_cells\":"<<zone.size()
                <<",\"H_m\":"<<H.value()<<",\"volume_m3\":"<<gSum(mesh.V())<<",\"source_route\":\"native_porosityForce_source_rho_U\",\"model_type\":\"grooveDarcy\",\"momentum_dimensions\":\"force\",\"pressure_matrix_symmetric\":true,\"pressure_matrix_positive_diagonal\":true,\"initial_p_max\":0,\"initial_U_max\":0}\n";checkStream(auditFile);
            Info<<"GDI_AUDIT_COMPLETE: native assembly only; zero solve calls"<<nl;return 0;
        }
        scalar initialRaw;{const tmp<scalarField> residual=pressure.residual();initialRaw=gSum(mag(residual()));}
        require(gdiFinite(initialRaw) && initialRaw>0,"Invalid zero-initial-pressure normalization");
        const SolverPerformance<scalar> perf=pressure.solve();
        p.correctBoundaryConditions();
        scalar raw;{const tmp<scalarField> residual=pressure.residual();raw=gSum(mag(residual()));}
        const scalar trueNorm=raw/initialRaw;
        surfaceScalarField phi(IOobject("phi",runTime.name(),mesh,IOobject::NO_READ,IOobject::AUTO_WRITE),phiHat+pressure.flux());
        U=HbyA-rAU*fvc::grad(p);U.correctBoundaryConditions();
        surfaceScalarField phiU(IOobject("phi_U",runTime.name(),mesh,IOobject::NO_READ,IOobject::AUTO_WRITE),fvc::flux(U));
        const volVectorField gradient(fvc::grad(p));
        const tmp<vectorField> force=model.force(U,rho,mu);
        scalar sumR2=0,maxR=0,sumDU2=0,maxDU=0,maxDP=0,energy=0;
        scalarField imbalance(mesh.nCells(),0);
        forAll(U,i)
        {
            const vector residual=force()[i]/mesh.V()[i]+gradient[i];
            const scalar du=mag(U[i]-oldU[i]);
            require(gdiFinite(mag(residual)) && gdiFinite(du) && gdiFinite(p[i]),"Nonfinite iteration state");
            sumR2+=magSqr(residual)*mesh.V()[i];maxR=max(maxR,mag(residual));
            sumDU2+=sqr(du)*mesh.V()[i];maxDU=max(maxDU,du);maxDP=max(maxDP,mag(p[i]-oldP[i]));energy+=(force()[i]&U[i]);
        }
        scalar net=0,leak=0,Qout=0,fluxDiff=0,fluxScale=0;
        forAll(mesh.neighbour(),fi){imbalance[mesh.owner()[fi]]+=phi[fi];imbalance[mesh.neighbour()[fi]]-=phi[fi];fluxDiff+=mag(phi[fi]-phiU[fi]);fluxScale+=mag(phi[fi]);}
        forAll(mesh.boundary(),pi)
        {
            const fvPatch& patch=mesh.boundary()[pi];if(patch.type()=="empty")continue;
            forAll(patch,li){const scalar q=phi.boundaryField()[pi][li];imbalance[patch.faceCells()[li]]+=q;net+=q;fluxDiff+=mag(q-phiU.boundaryField()[pi][li]);fluxScale+=mag(q);if(patch.name()=="xHigh")Qout+=q;if(patch.name()=="yLow"||patch.name()=="yHigh")leak+=mag(q);}
        }
        const scalar momL2=std::sqrt(sumR2/gSum(mesh.V()))/G,momMax=maxR/G;
        const scalar duL2=std::sqrt(sumDU2/gSum(mesh.V()))/scaleU.value(),duMax=maxDU/scaleU.value(),dP=maxDP/dp;
        const scalar global=mag(net)/Qs,local=sum(mag(imbalance))/Qs,side=leak/Qs,flux=fluxDiff/max(fluxScale,scalar(1e-300));
        const scalar power=dp*Qout,energyError=mag(energy-power)/max(mag(power),scalar(1e-300));
        history<<outer<<','<<perf.nIterations()<<','<<perf.finalResidual()<<','<<initialRaw<<','<<raw<<','<<trueNorm<<','<<momL2<<','<<momMax<<','<<duL2<<','<<duMax<<','<<dP<<','<<global<<','<<local<<','<<side<<','<<flux<<','<<energyError<<'\n';history.flush();checkStream(history);
        lastOuter=outer;lastLinear=perf.nIterations();lastNorm=perf.finalResidual();lastTrue=trueNorm;lastRaw=raw;
        const bool linearOK=gdiFinite(lastNorm)&&gdiFinite(lastTrue)&&lastNorm<=1e-12&&lastTrue<=1e-12&&lastLinear<=2000;
        converged=linearOK&&momL2<=1e-10&&momMax<=1e-10&&duL2<=1e-10&&duMax<=1e-10&&dP<=1e-10
            &&global<=1e-8&&local<=1e-8&&side<=1e-8&&flux<=1e-3&&energyError<=1e-3&&energy>=0&&power>0;
        const bool last=converged||!linearOK||outer==2000;
        if(last)
        {
            writeFieldsCSV(phi,phiU);
            std::ofstream evidence((out/"momentum_residual.csv").c_str());evidence<<std::setprecision(17);
            evidence<<"cell_id,old_Ux_m_s,old_Uy_m_s,old_Uz_m_s,old_p_Pa,diag_kg_s,source_x_N,source_y_N,source_z_N,grad_px_Pa_m,grad_py_Pa_m,grad_pz_Pa_m,force_x_N,force_y_N,force_z_N,pressure_matrix_raw_residual_m3_s\n";
            const tmp<scalarField> residual=pressure.residual();
            forAll(U,i){evidence<<i<<','<<oldU[i].x()<<','<<oldU[i].y()<<','<<oldU[i].z()<<','<<oldP[i]<<','<<momentum.diag()[i]<<','<<momentum.source()[i].x()<<','<<momentum.source()[i].y()<<','<<momentum.source()[i].z()<<','<<gradient[i].x()<<','<<gradient[i].y()<<','<<gradient[i].z()<<','<<force()[i].x()<<','<<force()[i].y()<<','<<force()[i].z()<<','<<residual()[i]<<'\n';}checkStream(evidence);evidence.close();
            volVectorField J(IOobject("J",runTime.name(),mesh,IOobject::NO_READ,IOobject::AUTO_WRITE),H*U);
            runTime.setTime(1,1);p.write();U.write();J.write();phi.write();phiU.write();
            break;
        }
    }
    std::ofstream stats((out/"solver.json").c_str());stats<<std::setprecision(17)
        <<"{\"protocol_id\":\"GDI-v1\",\"case_id\":\"GDI01\",\"run_id\":\""<<runId<<"\",\"solver\":\"grooveDarcyStaticFoam_Foundation13\",\"flow_solved\":true,\"converged\":"<<(converged?"true":"false")
        <<",\"outer_iterations\":"<<lastOuter<<",\"iterations\":"<<lastLinear<<",\"normalized_residual\":"<<lastNorm<<",\"true_normalized_residual\":"<<lastTrue<<",\"raw_residual_L1_m3_s\":"<<lastRaw
        <<",\"source_route\":\"native_porosityForce_source_rho_U\",\"model_type\":\"grooveDarcy\",\"porous_zone_cells\":512,\"pressure_matrix_sign\":-1,\"physical_time_advanced\":false,\"result_acceptance\":\"NOT_EVALUATED\"}\n";checkStream(stats);
    Info<<"GDI flow stage ended; external independent result acceptance required"<<nl;
    return converged?0:2;
}
