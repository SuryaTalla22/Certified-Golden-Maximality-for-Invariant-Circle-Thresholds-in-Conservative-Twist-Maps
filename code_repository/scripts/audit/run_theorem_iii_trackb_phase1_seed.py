#!/usr/bin/env python
from __future__ import annotations
import os
for _k in ["OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"]: os.environ.setdefault(_k,"1")
import argparse, json
from pathlib import Path
from kam_theorem_suite.lower_param.phase1_runner import run_phase1_grid

def flist(s): return [float(x.strip()) for x in str(s).split(',') if x.strip()]
def ilist(s): return [int(x.strip()) for x in str(s).split(',') if x.strip()]
def main():
    p=argparse.ArgumentParser(description="Track B Phase 1 diagnostic numerical seed solver for Theorem III lower-anchor work.")
    p.add_argument("--anchors",default="0.96630,0.96800,0.97000,0.97100,0.97150,0.9716350")
    p.add_argument("--resolutions",default="256,512,1024")
    p.add_argument("--workers",type=int,default=64)
    p.add_argument("--continuation-steps",type=int,default=40)
    p.add_argument("--max-newton",type=int,default=18)
    p.add_argument("--gmres-rtol",type=float,default=1e-11)
    p.add_argument("--gmres-atol",type=float,default=1e-13)
    p.add_argument("--gmres-restart",type=int,default=100)
    p.add_argument("--gmres-maxiter",type=int,default=800)
    p.add_argument("--newton-tol",type=float,default=1e-11)
    p.add_argument("--accept-linf",type=float,default=1e-8)
    p.add_argument("--nu",type=float,default=1.015)
    p.add_argument("--out-dir",default="artifacts/proof_audit/theorem_iii_trackb/phase1_seed")
    p.add_argument("--no-npz",action="store_true")
    p.add_argument("--force",action="store_true")
    a=p.parse_args()
    s=run_phase1_grid(anchors=flist(a.anchors),resolutions=ilist(a.resolutions),out_dir=Path(a.out_dir),workers=a.workers,continuation_steps=a.continuation_steps,max_newton=a.max_newton,gmres_rtol=a.gmres_rtol,gmres_atol=a.gmres_atol,gmres_restart=a.gmres_restart,gmres_maxiter=a.gmres_maxiter,newton_tol=a.newton_tol,accept_linf=a.accept_linf,nu=a.nu,write_npz=not a.no_npz,force=a.force)
    print(json.dumps({"status":s.get("status"),"counts":s.get("counts"),"summary":str(Path(a.out_dir)/"phase1_seed_summary.json"),"csv":str(Path(a.out_dir)/"phase1_seed_results.csv"),"best_by_anchor":s.get("best_by_anchor")},indent=2,sort_keys=True))
if __name__=="__main__": main()
