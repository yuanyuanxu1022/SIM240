# G2 Step 3 reuse audit

## Audited formal sources

- EX240 frozen source SHA-256:
  `4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002`
- Smooth75/G1-V2 frozen source SHA-256:
  `872630051336bab44f01efa65aaf920cb96c2e82ac5f754bd5fe03f9c80fa59d`
- repository commit at setup:
  `33494d161a53335b753865a04b31b5088801c743`

## Decision

The existing 2.5 nm Smooth75, G2-P, and G2-T results match the nominal
geometry, physical properties, acceleration, tau, boundary family, and
statistics required here. They are not formally reused in Step 3 because:

1. their result files do not save actual final `rho_min` and `rho_max`;
2. Step 3 therefore needs an added diagnostic field;
3. the user requires identical source version as a reuse condition.

The old results remain untouched and serve only as a post-run consistency
cross-check. All nine Step 3 points use one generated diagnostic source family
derived from the two frozen sources with audited, minimal changes.
