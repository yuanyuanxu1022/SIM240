# Section 2.1 properties, tau and time-step candidate (not merged)

Replace only the current property/time-step passage; retain the existing Eq. (1) number and surrounding text. This is a wording candidate, not renewed acceptance of run records.

The main comparisons and their refinements use a constant-property Newtonian liquid with density $\rho=1000$ kg m⁻³ and physical kinematic viscosity $\nu=1.0\times10^{-6}$ m²/s, giving dynamic viscosity $\mu=\rho\nu=1.0\times10^{-3}$ Pa·s. These are the properties adopted for the model. The two separately listed $\mu=15$ mPa·s checks are outside this main property setting.

For D3Q19, the squared sound speed in lattice units is $1/3$. With the dimensionless relaxation parameter $\tau=1$, the lattice kinematic viscosity is

$$
\nu^*=\frac{1}{3}\left(\tau-\tfrac12\right)=\frac{1}{6}.
$$

Lattice and physical kinematic viscosities satisfy $\nu=\nu^*\Delta x^2/\Delta t$. Given $\nu$, $\tau$ and grid spacing $\Delta x=5$ nm, the time step is therefore

$$
\Delta t=\frac{\left(\tau-\tfrac12\right)\Delta x^2}{3\nu}=4.1667\times10^{-12}\ \mathrm{s}
\tag{1}
$$

On refinement, physical density, physical kinematic viscosity and the dimensionless relaxation parameter are held fixed, while Eq. (1) sets the time step. Thus $\Delta t\propto\Delta x^2$: halving the spacing reduces the time step by a factor of four. This establishes consistency of the stated properties and unit conversion, rather than grid accuracy. No $\tau$ sensitivity sweep was performed, so relaxation-parameter independence is not claimed.
