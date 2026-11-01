"""依次运行 GeneralTools 与 SOITools 自检。

用法::

    python -m AIPLPhMTools.selftest.run_all
"""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    modules = [
        "AIPLPhMTools.selftest.general_tools",
        "AIPLPhMTools.selftest.soitools",
    ]
    failed = []
    for module in modules:
        print(f"\n===== {module} =====", flush=True)
        result = subprocess.run([sys.executable, "-m", module])
        if result.returncode != 0:
            failed.append(module)
    print("\n===== summary =====")
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    print("ALL SELFTESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
