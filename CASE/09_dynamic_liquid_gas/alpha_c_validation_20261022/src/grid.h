#pragma once
#include <olb.h>
#include <array>
#include <cmath>
#include <stdexcept>
#include <vector>

using Scalar=double;
using Vec=std::array<Scalar,3>;
using GridD=olb::descriptors::D3Q19<>;
struct Grid {
  int n;std::size_t size;
  explicit Grid(int length):n(length),size(std::size_t(n)*n*n){}
  int index(int x,int y,int z)const {
    auto wrap=[&](int v){return (v%n+n)%n;};return (wrap(x)*n+wrap(y))*n+wrap(z);
  }
  int neighbor(int x,int y,int z,int i,int sign=1)const {
    return index(x+sign*olb::descriptors::c<GridD>(i,0),
                 y+sign*olb::descriptors::c<GridD>(i,1),
                 z+sign*olb::descriptors::c<GridD>(i,2));
  }
  Scalar lap(const std::vector<Scalar>& f,int x,int y,int z)const {
    Scalar out=0;int p=index(x,y,z);
    for(int i=0;i<19;++i)out+=6*olb::descriptors::t<Scalar,GridD>(i)*(f[neighbor(x,y,z,i)]-f[p]);
    return out;
  }
  Vec grad(const std::vector<Scalar>& f,int x,int y,int z)const {
    Vec out{};
    for(int i=0;i<19;++i)for(int a=0;a<3;++a)
      out[a]+=3*olb::descriptors::t<Scalar,GridD>(i)*olb::descriptors::c<GridD>(i,a)*f[neighbor(x,y,z,i)];
    return out;
  }
  template<class F>void each(F fun)const {
    for(int x=0;x<n;++x)for(int y=0;y<n;++y)for(int z=0;z<n;++z)fun(x,y,z,index(x,y,z));
  }
};
inline Scalar dot(const Vec&a,const Vec&b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
inline Scalar norm(const Vec&a){return std::sqrt(dot(a,a));}
