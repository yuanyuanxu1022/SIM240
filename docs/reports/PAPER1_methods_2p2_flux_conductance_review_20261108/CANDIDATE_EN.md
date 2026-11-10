# Section 2.2 flux, driving and conductance candidate (not merged)

Replace the current definition passage while retaining Eq. (2). This candidate clarifies definitions, dimensions and reference height; it changes no conductance values and does not certify linearity over an enlarged domain.

Let $A_{\rm plan}=L_xL_y$ be the unit-cell area projected onto the substrate plane, $\Omega$ the three-dimensional fluid domain in the cell, and $u_i$ a physical velocity component. For separate nonzero principal-axis forcing in $i=x,y$, define

$$
J_i=\frac{1}{A_{\rm plan}}\int_\Omega u_i\,\mathrm dV,
\qquad
K_i=\frac{\mu J_i}{G_i},
\qquad G_i=\rho a_i\ne0.
\tag{2}
$$

$J_i$ is the depth-integrated flux normalized by the unit-cell plan area. The velocity volume integral has units m⁴/s; division by $A_{\rm plan}$ gives $J_i$ in m²/s. It is neither a volume-averaged velocity nor a total flow rate. The imposed uniform force per unit volume, $G_i$, has units Pa/m, equivalently N/m³. If expressed instead through an equivalent macroscopic pressure drop, the driving is $G_i=-\partial_i P_{\rm macro}$. This does not require the negative local pressure gradient to equal $\rho a_i$ everywhere in the periodic cell.

We call $K_i$ the depth-integrated conductance, in m³. Under the linear principal-direction relation $J_i=(K_i/\mu)G_i$, a larger $K_i$ gives a larger depth-integrated flux at the same viscosity and driving. This coefficient differs both from permeability in m² and from a coefficient defined as total flow rate divided by pressure drop.

With fluid volume $V_f=|\Omega|$, define the volume-equivalent reference height $H_{\rm ref}=V_f/A_{\rm plan}$. The equal groove and rib widths in the present rectangular geometry give $H_{\rm ref}=h+d/2$. For the fluid-volume-averaged velocity $\langle u_i\rangle_\Omega=V_f^{-1}\int_\Omega u_i\,\mathrm dV$,

$$
J_i=H_{\rm ref}\langle u_i\rangle_\Omega,
\qquad
\kappa_i\equiv\frac{\mu\langle u_i\rangle_\Omega}{G_i}
=\frac{K_i}{H_{\rm ref}}.
$$

Here, $\kappa_i$ is an effective permeability in m² defined using this reference height and averaging convention. Literature comparisons and coupling to other models must check both the reference height and whether velocity is averaged over fluid volume or is a superficial average over the entire reference volume. We compare $K_i$ using common volume-integral and projected-area definitions. Oblique-forcing responses use the corresponding tensor relation; the single-axis definition is not applied indiscriminately to arbitrary projections.
