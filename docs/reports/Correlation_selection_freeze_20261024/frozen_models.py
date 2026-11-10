"""Candidate closures for phi=0.5. Positive geometry; K uses h in metres."""
import numpy as np

def gains(s,t):
    s,t=np.broadcast_arrays(np.asarray(s,dtype=float),np.asarray(t,dtype=float))
    if np.any(s<=0) or np.any(t<0) or not np.all(np.isfinite(s+t)):
        raise ValueError('finite s>0 and t>=0 required')
    # Avoid cancellation at small depth.
    r=t*(3+t*(3+t))
    return r/2,r/(r+2)

def blend(x,y,m):
    x,y=np.broadcast_arrays(np.asarray(x,dtype=float),np.asarray(y,dtype=float))
    low=np.minimum(x,y);high=np.maximum(x,y)
    return low/(1+(low/high)**m)**(1/m)

def parts(s,t,fit):
    cp,ct=gains(s,t)
    pt=fit['T'];pp=fit['P']
    mt=pt[2] if len(pt)==3 else 1.
    mp=pp[2] if len(pp)==3 else 1.
    bt=np.exp(pt[0])*np.asarray(s)**pt[1]
    et=blend(ct,bt,mt)
    dp=np.exp(pp[0])*np.asarray(s)**pp[1]+np.asarray(s)**2*np.asarray(t)/2
    ep=et+blend(cp-et,dp,mp)
    return cp,ct,et,ep

def normalized(s,t,fit,direction):
    cp,ct=gains(s,t)
    if fit['model'].startswith('G'):
        _,_,et,ep=parts(s,t,fit)
        return 1+(ep if direction=='P' else et)
    al=1/np.asarray(s);be=np.asarray(t)/np.asarray(s)
    if np.any(be<=0):
        raise ValueError('C-series zero depth requires explicit flat endpoint')
    p=fit[direction];x=np.log(al);z=np.log(be)
    g=p[0]+p[1]*z+p[2]*x+(p[3]*x*x if len(p)==4 else 0)
    return (1+(cp if direction=='P' else ct))*np.exp(-np.logaddexp(0,g))

def derivative(s,t,fit,direction):
    cp,ct,et,ep=parts(s,t,fit)
    pt,pp=fit['T'],fit['P'];mt=pt[2] if len(pt)==3 else 1.;mp=pp[2] if len(pp)==3 else 1.
    bt=np.exp(pt[0])*np.asarray(s)**pt[1]
    dp=np.exp(pp[0])*np.asarray(s)**pp[1]+np.asarray(s)**2*np.asarray(t)/2
    ctprime=6*(1+np.asarray(t))**2/(2+2*cp)**2
    cpprime=1.5*(1+np.asarray(t))**2
    etprime=(et/ct)**(mt+1)*ctprime
    if direction=='T':return etprime
    extra=ep-et
    return etprime+(extra/(cp-et))**(mp+1)*(cpprime-etprime)+(extra/dp)**(mp+1)*np.asarray(s)**2/2
