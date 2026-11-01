"""LVS 脚本自检。

运行::

    python -m AIPLPhMTools.lvs_selftest

检查：
1. 一条连续直波导：同一 net 两个端子 → PASS；
2. 同一条直波导被拆成两个 net：短路 → FAIL；
3. CoupledRingFilter 的上下总线各自连通且互不短路 → PASS；
4. 故意写错的 CoupledRingFilter netlist → FAIL。
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import AIPLPhMTools as ap
from AIPLPhMTools.lvs import load_spec, run_lvs, terminals_from_component


def _check_component(name: str, spec: dict, expect_ok: bool, label: str) -> bool:
    c = ap.get_component(name)()
    gds = Path(tempfile.mkdtemp()) / f"{name}.gds"
    c.write_gds(str(gds))
    report = run_lvs(str(gds), spec, terminals_from_component(c))
    ok = report["ok"] is expect_ok
    print(("PASS " if ok else "FAIL ") + label +
          f"  [LVS {'PASS' if report['ok'] else 'FAIL'}, 期望 {'PASS' if expect_ok else 'FAIL'}]")
    return ok


def main() -> int:
    ok = True
    straight = {"layers": {"WG": [1, 0]}, "nets": {"line": ["o1", "o2"]}}
    ok &= _check_component("GfCStraight", straight, True, "直波导单 net")

    split = {"layers": {"WG": [1, 0]}, "nets": {"left": ["o1"], "right": ["o2"]}}
    ok &= _check_component("GfCStraight", split, False, "直波导拆两个 net（应短路）")

    spec = load_spec(Path(__file__).parent / "examples" / "lvs_coupled_filter.yaml")
    ok &= _check_component("CoupledRingFilter", spec, True, "CoupledRingFilter 正确 netlist")

    bad = load_spec(Path(__file__).parent / "examples" / "lvs_coupled_filter_bad.yaml")
    ok &= _check_component("CoupledRingFilter", bad, False, "CoupledRingFilter 错误 netlist")

    print("\nLVS SELFTEST " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
