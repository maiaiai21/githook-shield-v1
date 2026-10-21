#!/usr/bin/env python3
"""Score GitHook Shield's scanner against the labeled dataset.

Ground truth: each file in dataset/positives/ contains one synthetic secret;
each file in dataset/negatives/ contains none. A file counts as detected when
a tool reports at least one finding in it.

Compares our scanner (scanner/secretscan.py) with Gitleaks and detect-secrets
when they are installed. Writes results.json and results.md.

Run:  python3 evaluation/make_dataset.py && python3 evaluation/run_eval.py
"""
import json
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "scanner"))

import secretscan  # noqa: E402

POS = ROOT / "dataset" / "positives"
NEG = ROOT / "dataset" / "negatives"


def scan_ours(directory: Path):
    flagged = set()
    start = time.perf_counter()
    for path in sorted(directory.iterdir()):
        text = path.read_text(errors="replace")
        if secretscan.scan_text(text, path.name):
            flagged.add(path.name)
    return flagged, time.perf_counter() - start


def scan_gitleaks(directory: Path):
    if not shutil.which("gitleaks"):
        return None
    report = ROOT / "_gitleaks.json"
    start = time.perf_counter()
    subprocess.run(
        ["gitleaks", "detect", "--source", str(directory), "--no-git", "--no-banner", "--exit-code", "0",
         "--report-format", "json", "--report-path", str(report)],
        check=True, capture_output=True,
    )
    elapsed = time.perf_counter() - start
    findings = json.loads(report.read_text() or "null") if report.exists() else None
    report.unlink(missing_ok=True)
    
    flagged = set()
    if findings:
        for f in findings:
            filepath = f.get("file") or f.get("File")
            if filepath:
                flagged.add(Path(filepath).name)
                
    return flagged, elapsed


def scan_detect_secrets(directory: Path):
    if not shutil.which("detect-secrets"):
        return None
    start = time.perf_counter()
    proc = subprocess.run(
        ["detect-secrets", "scan", "--all-files", str(directory)],
        check=True, capture_output=True, text=True,
    )
    elapsed = time.perf_counter() - start
    data = json.loads(proc.stdout)
    flagged = {Path(p).name for p, results in data.get("results", {}).items() if results}
    return flagged, elapsed


def score(flagged, positives, negatives):
    tp = len(flagged & positives)
    fn = len(positives - flagged)
    fp = len(flagged & negatives)
    tn = len(negatives - flagged)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "tp": tp, "fn": fn, "fp": fp, "tn": tn,
        "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
        "missed_positives": sorted(positives - flagged),
        "false_positives": sorted(flagged & negatives),
    }


def per_category_recall(flagged, positives):
    totals, hits = defaultdict(int), defaultdict(int)
    for name in positives:
        category = name.split("_", 2)[2].rsplit(".", 1)[0]
        totals[category] += 1
        if name in flagged:
            hits[category] += 1
    return {c: f"{hits[c]}/{totals[c]}" for c in sorted(totals)}


def main():
    if not POS.exists() or not NEG.exists():
        sys.exit("Dataset missing. Run: python3 evaluation/make_dataset.py")

    positives = {p.name for p in POS.iterdir()}
    negatives = {n.name for n in NEG.iterdir()}

    tools = {"GitHook Shield (ours)": scan_ours,
             "Gitleaks": scan_gitleaks,
             "detect-secrets": scan_detect_secrets}

    results, timings, categories, skipped = {}, {}, {}, []
    for label, fn in tools.items():
        pos_run = fn(POS)
        neg_run = fn(NEG)
        if pos_run is None or neg_run is None:
            skipped.append(label)
            continue
        flagged = pos_run[0] | neg_run[0]
        results[label] = score(flagged, positives, negatives)
        timings[label] = [round(pos_run[1], 3), round(neg_run[1], 3)]
        categories[label] = per_category_recall(flagged, positives)

    out = {
        "dataset": {"positives": len(positives), "negatives": len(negatives)},
        "skipped_tools": skipped,
        "results": results,
        "scan_seconds": timings,
        "per_category_recall": categories,
    }
    (ROOT / "results.json").write_text(json.dumps(out, indent=2))

    lines = ["# Scanner evaluation results", "",
             f"Dataset: {len(positives)} files with one synthetic secret each, "
             f"{len(negatives)} files with none.", ""]
    if skipped:
        lines += [f"Not run (tool not installed): {', '.join(skipped)}", ""]
    lines += ["| Tool | TP | FN | FP | TN | Precision | Recall | F1 |",
              "|---|---|---|---|---|---|---|---|"]
    for label, r in results.items():
        lines.append(f"| {label} | {r['tp']} | {r['fn']} | {r['fp']} | {r['tn']} | "
                     f"{r['precision']} | {r['recall']} | {r['f1']} |")
    lines += ["", "## Recall by secret category", "",
              "| Category | " + " | ".join(results) + " |",
              "|---|" + "---|" * len(results)]
    all_cats = sorted({c for cats in categories.values() for c in cats})
    for c in all_cats:
        lines.append(f"| {c} | " + " | ".join(categories[t].get(c, "-") for t in results) + " |")
    lines += ["", "## Missed secrets", ""]
    for label, r in results.items():
        lines.append(f"- **{label}**: {', '.join(r['missed_positives']) or 'none'}")
    lines += ["", "## False positives", ""]
    for label, r in results.items():
        lines.append(f"- **{label}**: {', '.join(r['false_positives']) or 'none'}")
    lines += ["", "## Scan time, seconds (positives dir / negatives dir)", ""]
    for label, t in timings.items():
        lines.append(f"- **{label}**: {t[0]} / {t[1]}")
    (ROOT / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()