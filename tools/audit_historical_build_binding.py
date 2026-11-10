#!/usr/bin/env python3
"""
历史构建绑定可恢复性审计（只读）

目的：对补充材料表 S1 的 52 个 run 逐项检查，能恢复多少「构建来源」证据：
  A. run_manifest.txt 是否存在
  B. 清单登记的二进制路径是否仍存在，且 sha256 与清单、与表 S1 三重一致
  C. 清单登记的 generated_source 是否仍存在且 sha256 与清单一致
  D. 编译依赖文件 .d 是否存在，其 include 根目录是什么（用于绑定 OpenLB 树）
  E. 该 .d 列出的 OpenLB 头文件今日是否仍全部存在

不修改任何文件，不运行求解器，不写「已恢复」以外的判定。
"""
import csv
import hashlib
import json
import os
import re

ROOT = "/home/dell/yuanyuanxu/SIM240"
S1 = os.path.join(ROOT, "docs/reports/SIM240_Supplementary_Methods_20261024/Table_S1_run_inventory.csv")
OUT = os.path.join(ROOT, "docs/reports/Historical_build_binding_recovery_20261028")

HEX64 = re.compile(r"^([0-9a-f]{64})\s+(\S+)$")


def sha256(path, limit=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_manifest(path):
    """两代清单格式并存：
    旧式：'<sha256>  <abs_path>'（sha256sum 风格）
    新式：'binary=/abs/path' + 'binary_sha256=<hash>'（key=value）
    返回 (hashes{path:sha}, kv{key:value})。
    """
    hashes = {}
    kv = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            m = HEX64.match(s)
            if m:
                hashes[m.group(2)] = m.group(1)
                continue
            if "=" in s and not s.startswith("#"):
                k, _, v = s.partition("=")
                kv[k.strip()] = v.strip()
    # 把 key=value 里的 binary/binary_sha256 也归一成 hashes 条目
    b = kv.get("binary")
    h = kv.get("binary_sha256")
    if b and h:
        hashes.setdefault(b, h)
    return hashes, kv


def resolve_old_path(old, manifest_path):
    """旧绝对路径可能因 CASE 目录加编号前缀而失效，尝试用文件名在邻近 build 目录中定位。"""
    if os.path.exists(old):
        return old, "EXACT_PATH"
    base = os.path.basename(old)
    # 在清单所在 run 目录向上找到该 case 根，再全 case 子树搜同名文件
    case_root = manifest_path
    for _ in range(8):
        case_root = os.path.dirname(case_root)
        if os.path.basename(os.path.dirname(case_root)) == "CASE":
            case_root = os.path.dirname(case_root)
            break
    cands = []
    for dirpath, _dirnames, filenames in os.walk(ROOT):
        if "/CASE/" not in dirpath + "/":
            continue
        if base in filenames:
            cands.append(os.path.join(dirpath, base))
    if len(cands) == 1:
        return cands[0], "UNIQUE_BASENAME_MATCH"
    if len(cands) > 1:
        return None, f"AMBIGUOUS_{len(cands)}_CANDIDATES"
    return None, "NOT_FOUND"


def dep_roots(dep_file):
    roots = set()
    with open(dep_file, encoding="utf-8", errors="replace") as f:
        txt = f.read().replace("\\\n", " ")
    for tok in txt.split():
        tok = tok.rstrip("\\:")
        if tok.startswith("/home/") or tok.startswith("/opt/"):
            if "/openlb/" in tok:
                roots.add(tok.split("/openlb/")[0] + "/openlb")
    return sorted(roots)


def dep_headers(dep_file):
    out = []
    with open(dep_file, encoding="utf-8", errors="replace") as f:
        txt = f.read().replace("\\\n", " ")
    for tok in txt.split():
        tok = tok.rstrip("\\:")
        if "/openlb/" in tok:
            out.append(tok)
    return sorted(set(out))


def main():
    rows = list(csv.DictReader(open(S1, encoding="utf-8")))
    results = []
    summary = {
        "runs_in_s1": len(rows),
        "manifest_present": 0,
        "binary_present": 0,
        "binary_hash_triple_match": 0,
        "generated_source_present": 0,
        "generated_source_hash_match": 0,
        "dep_file_present": 0,
        "openlb_root_consistent": 0,
        "all_listed_headers_present": 0,
    }
    openlb_roots = {}
    for r in rows:
        mp = os.path.join(ROOT, r["manifest_path"])
        rec = {
            "run_id": r["run_id"],
            "group": r["group"],
            "manifest": r["manifest_path"],
            "manifest_exists": os.path.exists(mp),
        }
        if not rec["manifest_exists"]:
            rec["status"] = "MANIFEST_MISSING"
            results.append(rec)
            continue
        summary["manifest_present"] += 1
        hashes, kv = parse_manifest(mp)
        rec["manifest_hash_entries"] = len(hashes)
        rec["manifest_keys"] = sorted(kv.keys())

        # --- B: 二进制 ---
        bin_old = kv.get("binary")
        if not bin_old:
            for old in hashes:
                if "/build/" in old and not old.endswith(
                    (".cpp", ".md", ".txt", ".h", ".o", ".d")
                ):
                    bin_old = old
                    break
        if bin_old:
            rec["manifest_binary_path"] = bin_old
            rec["manifest_binary_sha256"] = hashes.get(bin_old)
            resolved, how = resolve_old_path(bin_old, mp)
            rec["binary_resolved"] = resolved
            rec["binary_resolution"] = how
            if resolved:
                summary["binary_present"] += 1
                actual = sha256(resolved)
                rec["binary_actual_sha256"] = actual
                rec["binary_matches_manifest"] = actual == hashes.get(bin_old)
                rec["binary_matches_S1"] = actual == r["binary_sha256"]
                rec["binary_triple_match"] = bool(
                    rec["binary_matches_manifest"] and rec["binary_matches_S1"]
                )
                if rec["binary_triple_match"]:
                    summary["binary_hash_triple_match"] += 1
                rec["build_dir"] = os.path.dirname(resolved) or None

        # --- C: 生成源码 ---
        gen_old = None
        for old in hashes:
            if old.endswith(".cpp"):
                gen_old = old
                break
        if gen_old:
            rec["manifest_generated_source"] = gen_old
            rec["manifest_generated_sha256"] = hashes[gen_old]
            resolved, how = resolve_old_path(gen_old, mp)
            rec["generated_resolved"] = resolved
            rec["generated_resolution"] = how
            if resolved:
                summary["generated_source_present"] += 1
                actual = sha256(resolved)
                rec["generated_actual_sha256"] = actual
                rec["generated_matches_manifest"] = actual == hashes[gen_old]
                if rec["generated_matches_manifest"]:
                    summary["generated_source_hash_match"] += 1

        # --- D/E: 编译依赖文件 .d（在 build 目录内递归查找） ---
        dep = None
        search_dirs = []
        if rec.get("build_dir"):
            search_dirs.append(rec["build_dir"])
        if rec.get("generated_resolved"):
            search_dirs.append(os.path.dirname(rec["generated_resolved"]))
        for sd in search_dirs:
            if not sd or not os.path.isdir(sd):
                continue
            found = []
            for dirpath, _dn, fns in os.walk(sd):
                for fn in fns:
                    if fn.endswith(".d"):
                        found.append(os.path.join(dirpath, fn))
            if found:
                # 优先与二进制同名
                bname = os.path.basename(rec.get("binary_resolved") or "")
                pref = [p for p in found if os.path.basename(p)[:-2] == bname]
                dep = (pref or sorted(found, key=len))[0]
                break
        if dep:
            summary["dep_file_present"] += 1
            rec["dep_file"] = os.path.relpath(dep, ROOT)
            roots = dep_roots(dep)
            rec["openlb_roots"] = roots
            for rt in roots:
                openlb_roots[rt] = openlb_roots.get(rt, 0) + 1
            if roots == ["/home/dell/openlb"]:
                summary["openlb_root_consistent"] += 1
                rec["openlb_root_consistent"] = True
            headers = dep_headers(dep)
            missing = [h for h in headers if not os.path.exists(h)]
            rec["dep_header_count"] = len(headers)
            rec["dep_headers_missing"] = len(missing)
            rec["dep_headers_missing_sample"] = missing[:5]
            if not missing and headers:
                summary["all_listed_headers_present"] += 1
                rec["dep_headers_all_present"] = True
        results.append(rec)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "binding_recovery.json"), "w", encoding="utf-8") as f:
        json.dump(
            {"summary": summary, "openlb_roots_seen": openlb_roots, "runs": results},
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("=== 汇总 ===")
    for k, v in summary.items():
        print(f"{k}: {v}")
    print("=== 出现过的 OpenLB 根 ===")
    for k, v in openlb_roots.items():
        print(f"  {k}  ({v} 次)")
    print(f"\n明细已写入 {OUT}/binding_recovery.json")


if __name__ == "__main__":
    main()
