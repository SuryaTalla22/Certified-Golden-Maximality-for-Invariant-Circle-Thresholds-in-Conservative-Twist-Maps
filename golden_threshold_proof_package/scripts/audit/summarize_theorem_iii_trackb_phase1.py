#!/usr/bin/env python
from __future__ import annotations
import argparse,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description="Print a compact Track-B Phase-1 seed report.")
    p.add_argument("summary",nargs="?",default="artifacts/proof_audit/theorem_iii_trackb/phase1_seed/phase1_seed_summary.json")
    p.add_argument("--top",type=int,default=20); a=p.parse_args()
    d=json.loads(Path(a.summary).read_text()); rows=d.get("records",[])
    rows.sort(key=lambda r:(float(r.get("residual_linf") or 1e300),float(r.get("config",{}).get("K_target",0))))
    print(json.dumps({"status":d.get("status"),"counts":d.get("counts"),"parameters":d.get("parameters"),"best_by_anchor":d.get("best_by_anchor"),"top_records_by_residual":[{"K":r.get("config",{}).get("K_target"),"M":r.get("config",{}).get("M"),"converged":r.get("converged"),"status":r.get("solve_status"),"residual_linf":r.get("residual_linf"),"residual_l1_nu":r.get("residual_l1_nu"),"tail_ratio_top_10pct":r.get("tail_ratio_top_10pct"),"strip_width":r.get("estimated_strip_width"),"npz":r.get("output_npz")} for r in rows[:max(1,a.top)]]},indent=2,sort_keys=True))
if __name__=="__main__": main()
