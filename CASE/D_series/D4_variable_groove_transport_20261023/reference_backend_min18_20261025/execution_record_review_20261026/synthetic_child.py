"""Fixed short fixture only; never imports a project solver."""
from pathlib import Path
import sys

print("synthetic stdout complete", flush=True)
print("synthetic stderr complete", file=sys.stderr, flush=True)
Path("partial_synthetic.bin").write_bytes(b"partial fixture retained\n")
raise SystemExit(7)
