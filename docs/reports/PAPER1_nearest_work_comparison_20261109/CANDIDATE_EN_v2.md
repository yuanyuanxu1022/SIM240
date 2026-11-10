# Recently related work: English candidate (round-2 revision, not merged)

2026-11-09 (evening). This file supersedes `CANDIDATE_EN.md`; the round-1 file is left unchanged. Evidence and corrections: `ROUND2_VERIFICATION.md`.

Citation numbers are placeholders (`[Ng]`, `[MF]`, `[St]`) for the reason given in `ROUND2_VERIFICATION.md` §8: the current manuscript states that references are numbered in order of first appearance, so reusing `[12]`–`[15]` from round 1 would make that statement false; and the target journal is not yet fixed, so an author–year style would discard the numbering entirely. Settle it once, at merge time.

---

## Insertion point

English manuscript §1.2 has three paragraphs. Insert **after the second paragraph** (the one ending "…is therefore not itself a new finding."), as a new third paragraph; the existing third paragraph ("The compared problems and coefficient definitions differ…") then follows.

---

## Candidate text (English)

> Solutions for rectangular grooves closer to the present geometry also exist. Ng[Ng] solved no-slip pressure-driven Stokes flow between two walls each patterned with rectangular grooves, using domain decomposition and eigenfunction matching, and reported flow rates and effective slip lengths for flow along and transverse to the grooves while varying the phase shift between the two patterns. The present equal-width grooves and ridges correspond to his groove area fraction of 0.5. The two are nevertheless not the same boundary-value problem: in his symmetric configuration the mid-plane is a plane of zero shear by geometric symmetry, whereas the upper boundary here is a no-slip plate; and his effective slip lengths are defined from the clear-layer flow between the two wall envelopes, explicitly excluding the groove volume for the longitudinal case, so they do not convert into the present depth-integrated conductance that includes all fluid. He further notes that semi-analytical effective slip lengths for rectangular grooves were given earlier by Wang for a semi-infinite fluid, and that Wang, although also considering channels with grooved walls, did not examine the effect of wall spacing. Two of Ng's[Ng] conclusions bear directly on this study: the longitudinal flow rate always exceeds the transverse one; and the effect of wall spacing on the slip length persists until the walls are separated by 10–10³ pattern periods. The gap-to-period ratio of the present geometry is 0.10–0.52, squarely within his confinement-dominated range; this is the reason the present study uses a finite-gap family rather than citing slip results for a semi-infinite grooved surface.
>
> Regarding pressure losses, Mohammadi and Floryan[MF] analysed losses produced by small-amplitude two-dimensional grooves, separating them into a change in the mean wall positions, obtained analytically, and a flow-modulation part that requires numerical evaluation and can be captured with a Fourier leading-mode model to within 10% in most cases; they found a strong dependence on groove orientation, with longitudinal grooves giving the smallest drag. Their detailed parameter results are for sinusoidal grooves and are exact for that profile; rectangular grooves do fall within their scope, but only as a test of the convergence of the reduced model, a single retained mode being up to 50% in error. The actual limit is one of amplitude: their upper bound is 0.06 normalised by the half-channel height, whereas the equivalent amplitude here is 0.36--2.67, i.e. 6--44 times larger (the depth-to-gap ratio reaches 4.0). Stroock et al.[St] gave anisotropic effective boundary conditions for shallow grooved surfaces and showed that pressure-driven flow over grooves develops transverse components, with experimental checks of their model. Groove-induced transverse flow and anisotropic effective boundaries are therefore not the novelty of the present work.

Length: about 400 words. This is longer than the round-1 candidate; the additions are Ng's two quantitative conclusions and the gap-to-period argument.

---

## Relation to the existing third paragraph

The final sentence ("Groove-induced transverse flow … are therefore not the novelty of the present work") sets up the existing third paragraph, which ends with the contribution statement. **If this reads as repetitive, delete the final sentence** and let the third paragraph carry the turn; both versions are coherent, the shorter one is tighter.

---

## Four items to synchronise at merge time

1. **Reference list**: apply the chosen numbering scheme (`ROUND2_VERIFICATION.md` §8, option A or B); bibliographic entries are [12]–[14] in `REFERENCES.md`; replace the placeholders.
2. **Supplementary S11**: record the two changes in reading level from this round — Ng is now held as a local full text (not merely a web reader); Stroock reaches publisher-abstract level only, with all three full-text routes refused. Any S11 wording asserting a full-text read must be corrected.
3. **Appendix B** (traceability of numbers): this passage introduces no new result. If the quantities "10–10³ periods" and "0.10–0.52" are retained, note their provenance — the former from Ng §3 (final paragraph) and §4, the latter computed from the $h$ values in Table 1 divided by $P=240$ nm.
4. **Chinese manuscript**: use `CANDIDATE_CN_v2.md` and merge both in the same pass; otherwise the two language versions drift again.

---

## Three things this passage must not do

1. **No "first".** Directionality and finite-spacing effects are covered in prior work; the present increment is an assessment of a specific reduced construction, not the discovery of groove anisotropy.
2. **No ranking.** Do not state that Ng's results are more or less accurate than those here, and do not quote a percentage difference against them. The normalisations differ, so any difference would be an artefact.
3. **No borrowed detail from the Stroock abstract.** No page numbers, equation numbers or amplitude symbols; describe the profile only as "shallow grooves", not as sinusoidal or cosinusoidal. The latter detail can be traced only to the description in [5], not to a direct reading of Stroock et al.
