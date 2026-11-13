# Freeze log

- 2026-11-13T15:16:02Z release `8710a757c3e09a2fb1227b6eb8c72dbbf00cf810d23a102c0069280078e82c6a` files=14 reason: initial freeze before any run: 14 T points, h25 scope pending
- 2026-11-13T15:16:43Z release `ff8385b0ee3c758a88200c2a3cc9be4527e8604f0c903c52f4233e9dc1fce50a` files=14 reason: unify file collection in receipt.py and add completeness check; no run has occurred
- 2026-11-13T15:17:26Z release `128c6e7992cd5d500b6ea5da38e288928a4a3789935b530461b7ab11e7a64708` files=15 reason: add stubbed-solver control-flow tests; still no physics run
- 2026-11-13T15:17:36Z release `f9e45934e57f499009b3e292bd65cf0e8a48cfc2fc9e05b152be8a3d7b437134` files=15 reason: fix first-level probe in stubbed control-flow test; no physics run
- 2026-11-13T15:18:19Z release `809681a2f16d7ce6cd508fff5f46f35327b27e64ed7f21a1e948bec6de61cde5` files=16 reason: add finiteness and section-count checks in the v2 wrapper (v1 verifier untouched); no run yet
- 2026-11-13T15:27:56Z release `cdbf97fd0e490b4cc047fe70954eefafa4ac42b7e128cffa657fc6ca27eb4e83` files=21 reason: assessor recomputes every label from the saved fields; one attempt per case; verification receipt written once; exit code and mesh-JSON hash checked (no run has occurred)
- 2026-11-13T15:30:30Z release `72e59366a526d8aa043d43971fcb01b2668acef64ef6367e307bad9cf85e1f20` files=22 reason: lead check: assessor records malformed fields as NOT_RECONSTRUCTIBLE instead of aborting the table; regression test added (no run has occurred)
- 2026-11-13T15:30:57Z release `2e6a6c9cff48ec630ed683c000921229b0ba300c14188268be3cdb07edf10f91` files=22 reason: README documents the trust structure: receipts are not the anchor, the assessor recomputes from fields, and the mechanism limits forgery but does not prevent it (no run has occurred)
- 2026-11-13T15:31:59Z release `26cfd75d5739b2afe9522036dcab1e30544b23aa35f7ef4a0d280c7689ca8cfe` files=22 reason: README end-of-file blank line removed for git diff --check; content unchanged (no run has occurred)
