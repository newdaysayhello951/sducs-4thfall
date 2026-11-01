"""校验 metrics.py 的 R / S / F 实现。

官方评测脚本是 Perl（数据集 evaluation/EVAL_TOPICDETECTION_RS.pl）。本机若无
perl，则退化为两路校验：

  1. 独立朴素实现：逐条照抄官方脚本的双重循环结构（O(n^2)），与 metrics.py
     里基于 Counter 的向量化实现在同一份数据上比对，确保两者数值一致。
  2. 解析解用例：构造 R/S 可以手算的小例子，验证语义正确。

用法::

    python -m src.validate_metrics
"""

from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "data" / "raw" / "replab2013-dataset" / "evaluation"
GOLD = EVAL_DIR / "examples" / "topicDetection.GOLD.dat"
SYS = EVAL_DIR / "examples" / "topicDetection.SYS.dat"
PERL_SCRIPT = EVAL_DIR / "EVAL_TOPICDETECTION_RS.pl"

sys.path.insert(0, str(ROOT))
from src.metrics import score_entity  # noqa: E402


# ---------------------------------------------------------------- 独立朴素实现
# 刻意按官方 Perl 的循环结构逐句转写，作为对照基准。

def naive_score(gold: Sequence[str], sys_labels: Sequence[Optional[str]]) -> Tuple[float, float, float]:
    n = len(gold)
    if n == 0:
        return 0.0, 0.0, 0.0
    s = list(sys_labels)
    total_r = 0.0
    total_s = 0.0
    for i in range(n):
        # Sensitivity
        samp_sd = 0
        sd = 0
        for j in range(n):
            if gold[j] == gold[i]:
                samp_sd += 1
                if s[i] is not None and s[j] is not None and s[i] == s[j]:
                    sd += 1
        total_s += sd / samp_sd if samp_sd > 0 else 1.0
        # Reliability
        samp_rd = 0
        rd = 0
        for j in range(n):
            if s[i] is not None and s[j] is not None and s[i] == s[j]:
                samp_rd += 1
                if gold[j] == gold[i]:
                    rd += 1
        total_r += rd / samp_rd if samp_rd > 0 else 1.0
    R = total_r / n
    S = total_s / n
    F = 2 * R * S / (R + S) if (R > 0 and S > 0) else 0.0
    return R, S, F


# ---------------------------------------------------------------- 解析解用例

def analytic_cases() -> List[Tuple[str, Sequence[str], Sequence[Optional[str]], Tuple[float, float, float]]]:
    """每个用例的 (R, S, F) 都可手算验证。"""
    return [
        # 完美聚类
        ("perfect", ["a", "a", "b"], ["x", "x", "y"], (1.0, 1.0, 1.0)),
        # 全部并成一簇：S=1；R = (2/3 + 2/3 + 1/3)/3
        ("one_cluster", ["a", "a", "b"], ["z", "z", "z"], ((2 / 3 + 2 / 3 + 1 / 3) / 3, 1.0, None)),
        # 全部分开：R=1；S = (1/2 + 1/2 + 1)/3
        ("all_singletons", ["a", "a", "b"], ["x", "y", "z"], (1.0, (0.5 + 0.5 + 1.0) / 3, None)),
        # 系统漏掉一条。按官方脚本语义：
        #   doc0 正常：S 计 1/2，R 计 1/1
        #   doc1 缺失：S 计 0，  R 计 1（官方脚本对缺失文档给 Reliability 记满分）
        #   => R=1.0, S=0.25, F=0.4
        ("missing_doc", ["a", "a"], ["x", None], (1.0, 0.25, 0.4)),
    ]


def run_analytic() -> bool:
    ok = True
    for name, gold, sysl, expected in analytic_cases():
        sc = score_entity(name, gold, sysl)
        got = (sc.reliability, sc.sensitivity, sc.f1)
        for k, key in enumerate(("R", "S", "F")):
            if expected[k] is None:
                continue
            if abs(got[k] - expected[k]) > 1e-9:
                print(f"  [FAIL] {name} {key}: got {got[k]:.6f}, want {expected[k]:.6f}")
                ok = False
    print("解析解用例：" + ("全部通过 ✅" if ok else "存在失败 ❌"))
    return ok


# ---------------------------------------------------------------- 真实数据比对

def read_triples(path: Path) -> Dict[str, List[Tuple[str, str]]]:
    out: Dict[str, List[Tuple[str, str]]] = {}
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        reader = csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_ALL)
        next(reader, None)
        for row in reader:
            if len(row) < 3:
                continue
            out.setdefault(row[0], []).append((row[1], row[2]))
    return out


def run_perl() -> Optional[Dict[str, Tuple[float, float, float]]]:
    if shutil.which("perl") is None:
        return None
    proc = subprocess.run(
        ["perl", str(PERL_SCRIPT), str(GOLD), str(SYS)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        print(f"  Perl 执行失败：{proc.stderr[:300]}")
        return None
    res = {}
    for line in proc.stdout.splitlines()[1:]:
        p = line.split("\t")
        if len(p) >= 5 and p[1] != "average":
            res[p[1]] = (float(p[2]), float(p[3]), float(p[4]))
    return res


def main() -> int:
    print("=" * 60)
    print("1) 解析解用例")
    ok = run_analytic()

    if not GOLD.exists():
        print(f"缺少示例文件 {GOLD}，跳过真实数据比对")
        return 0 if ok else 1

    gold = read_triples(GOLD)
    sysd = {e: dict(v) for e, v in read_triples(SYS).items()}

    print("\n2) 真实示例数据：metrics.py vs 朴素独立实现")
    worst = 0.0
    for ent, rows in sorted(gold.items()):
        g = [t for _, t in rows]
        s = [sysd.get(ent, {}).get(tid) for tid, _ in rows]
        a = score_entity(ent, g, s)
        b = naive_score(g, s)
        worst = max(worst, abs(a.reliability - b[0]), abs(a.sensitivity - b[1]), abs(a.f1 - b[2]))
    print(f"  实体数 {len(gold)}，最大绝对误差 {worst:.3e} " + ("✅" if worst < 1e-12 else "❌"))
    ok = ok and worst < 1e-12

    print("\n3) 与官方 Perl 脚本比对")
    perl = run_perl()
    if perl is None:
        print("  本机没有 perl，跳过（已用朴素实现交叉验证）")
    else:
        diff = 0.0
        for ent, rows in gold.items():
            g = [t for _, t in rows]
            s = [sysd.get(ent, {}).get(tid) for tid, _ in rows]
            a = score_entity(ent, g, s)
            if ent in perl:
                diff = max(diff, abs(a.reliability - perl[ent][0]),
                           abs(a.sensitivity - perl[ent][1]), abs(a.f1 - perl[ent][2]))
        print(f"  最大绝对误差 {diff:.3e} " + ("✅" if diff < 1e-9 else "❌"))
        ok = ok and diff < 1e-9

    print("=" * 60)
    print("结论：" + ("指标实现通过校验" if ok else "指标实现存在问题"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
