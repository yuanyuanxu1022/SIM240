// SPDX-License-Identifier: GPL-3.0-or-later
#include "../src/grooveTransport.H"
#include <iostream>
#include <limits>
#include <vector>
int main()
{
    int checks=0;
    auto close=[&](double a,double b) { ++checks; if(std::abs(a/b-1)>1e-12) throw std::runtime_error("coefficient test failed"); };
    for(double h : {25e-9,75e-9,150e-9}) for(bool v2 : {false,true})
    {
        auto r=sim240::transport(h,0,120e-9,240e-9,v2);
        close(r.H,h); close(r.Kparallel,h*h*h/12); close(r.Kperpendicular,h*h*h/12);
        close(r.Dparallel,12/(h*h)); close(r.Dperpendicular,12/(h*h));
    }
    const auto r=sim240::transport(75e-9,100e-9,120e-9,240e-9,true);
    close(r.H,125e-9); close(r.Kparallel,1.0414014079511954e-22); close(r.Kperpendicular,4.5537951695675916e-23);
    close(r.Dparallel,1200305655874992.2); close(r.Dperpendicular,2744963164688618.5);
    const double nan=std::numeric_limits<double>::quiet_NaN();
    for(auto a : std::vector<std::vector<double>>{{0,100e-9,120e-9,240e-9},{-1,0,120e-9,240e-9},{nan,0,120e-9,240e-9},{75e-9,-1,120e-9,240e-9},{75e-9,100e-9,100e-9,240e-9},{75e-9,100e-9,240e-9,480e-9}})
    {
        bool rejected=false;
        try {sim240::transport(a[0],a[1],a[2],a[3],true);}
        catch(const std::invalid_argument&) {rejected=true;}
        if(!rejected) throw std::runtime_error("invalid geometry accepted");
        ++checks;
    }
    std::cout<<"COEFFICIENT_PASS checks="<<checks<<"\n";
}
