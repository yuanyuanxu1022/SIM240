#include "movingPistonConversion.h"
#include <cmath>
#include <iostream>
#include <vector>
struct FSCell { Phase type; int flags; bool hasNbr; double prev[3]; double mass,eps; };
static bool convertOne(std::vector<FSCell>& c,int src,int dst) {
  auto backup=c; double m=c[src].mass,e=c[src].eps,cap=1-c[dst].eps;
  if(cap+1e-14<e) return false;
  c[dst].eps+=e; c[dst].mass+=m; c[src].eps=0; c[src].mass=0; c[src].type=Phase::Solid; c[src].flags=0; c[src].hasNbr=false; c[src].prev[0]=c[src].prev[1]=c[src].prev[2]=0;
  c[dst].type=(c[dst].eps>=1-1e-12?Phase::Fluid:Phase::Interface); c[dst].flags=1; c[dst].hasNbr=true;
  if(c[dst].eps<0||c[dst].eps>1){c=backup;return false;} return true;
}
int main(){
  std::vector<FSCell> c(3, {Phase::Fluid,1,true,{0,0,0},1,1});
  c[0]={Phase::Interface,3,true,{0.2,0,0},0.5,0.5}; c[1]={Phase::Interface,3,true,{0,0,0},0.25,0.25}; c[2]={Phase::Fluid,3,true,{0,0,0},1,1};
  double m0=0,v0=0;for(auto&x:c){m0+=x.mass;v0+=x.eps;} if(!convertOne(c,0,1))return 1; double m1=0,v1=0;for(auto&x:c){m1+=x.mass;v1+=x.eps;} if(std::abs(m1-m0)>1e-12||std::abs(v1-v0)>1e-12||c[0].type!=Phase::Solid||c[0].hasNbr)return 1;
  auto before=c; if(convertOne(c,1,2))return 1; if(c[1].eps!=before[1].eps||c[1].mass!=before[1].mass)return 1;
  std::cout<<"M3 FreeSurface single-step integration test passed\n"; return 0;
}
