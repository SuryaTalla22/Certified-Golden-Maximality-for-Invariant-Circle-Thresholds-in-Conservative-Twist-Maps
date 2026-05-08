from __future__ import annotations
import csv, json, os, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from .standard_sine_embedding import SeedSolveConfig, solve_anchor_with_continuation, write_json

def _cfg_dict(cfg: SeedSolveConfig) -> dict[str, Any]:
    return {name: getattr(cfg, name) for name in SeedSolveConfig.__dataclass_fields__}

def _task(cfgd: dict[str,Any], out_dir: str, write_npz: bool, force: bool) -> dict[str,Any]:
    for k in ["OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"]:
        os.environ.setdefault(k,"1")
    cfg=SeedSolveConfig(**cfgd); out=Path(out_dir)
    tag=f"K{cfg.K_target:.10f}_M{cfg.M}_steps{cfg.continuation_steps}".replace(".","p")
    jp=out/"records"/f"{tag}.json"; npz=out/"embeddings"/f"{tag}.npz" if write_npz else None
    if jp.exists() and not force:
        try:
            d=json.loads(jp.read_text()); d["loaded_from_existing_record"]=True; return d
        except Exception: pass
    r=solve_anchor_with_continuation(cfg,out_npz=npz); d=r.to_dict(); d["record_path"]=str(jp); write_json(jp,d); return d

def run_phase1_grid(*, anchors:list[float], resolutions:list[int], out_dir:str|Path, workers:int=1, continuation_steps:int=36, max_newton:int=16, gmres_rtol:float=1e-11, gmres_atol:float=1e-13, gmres_restart:int=80, gmres_maxiter:int=600, newton_tol:float=1e-11, accept_linf:float=1e-8, nu:float=1.015, write_npz:bool=True, force:bool=False) -> dict[str,Any]:
    t0=time.time(); out=Path(out_dir); (out/"records").mkdir(parents=True,exist_ok=True); (out/"embeddings").mkdir(parents=True,exist_ok=True)
    tasks=[]
    for K in anchors:
        for M in resolutions:
            tasks.append(_cfg_dict(SeedSolveConfig(K_target=float(K), M=int(M), continuation_steps=continuation_steps, max_newton=max_newton, gmres_rtol=gmres_rtol, gmres_atol=gmres_atol, gmres_restart=gmres_restart, gmres_maxiter=gmres_maxiter, newton_tol=newton_tol, accept_linf=accept_linf, nu=nu)))
    rows=[]; nw=max(1,min(int(workers),len(tasks))) if tasks else 1
    if nw==1:
        for td in tasks: rows.append(_task(td,str(out),write_npz,force))
    else:
        with ProcessPoolExecutor(max_workers=nw) as ex:
            futs=[ex.submit(_task,td,str(out),write_npz,force) for td in tasks]
            for fut in as_completed(futs):
                row=fut.result(); rows.append(row); cfg=row.get("config",{})
                print(f"[phase1] K={float(cfg.get('K_target',float('nan'))):.10f} M={int(cfg.get('M',-1))} converged={row.get('converged')} status={row.get('solve_status')} residual_linf={row.get('residual_linf')}", flush=True)
    rows.sort(key=lambda r:(float(r.get("config",{}).get("K_target",0.0)), int(r.get("config",{}).get("M",0))))
    best={}
    for r in rows:
        key=f"{float(r.get('config',{}).get('K_target',0.0)):.10f}"
        if key not in best or float(r.get("residual_linf") or 1e300) < float(best[key].get("residual_linf") or 1e300): best[key]=r
    summary={"schema":"theorem_iii_trackb_phase1_grid_summary_v1","phase":"TrackB-Phase1-numerical-seed","diagnostic_only":True,"theorem_facing":False,"promotion_allowed":False,"status":"phase1-seed-scan-complete" if rows else "no-tasks","parameters":{"anchors":anchors,"resolutions":resolutions,"workers_requested":workers,"workers_used":nw,"continuation_steps":continuation_steps,"max_newton":max_newton,"gmres_rtol":gmres_rtol,"gmres_atol":gmres_atol,"gmres_restart":gmres_restart,"gmres_maxiter":gmres_maxiter,"newton_tol":newton_tol,"accept_linf":accept_linf,"nu":nu},"counts":{"tasks":len(tasks),"completed_records":len(rows),"converged":sum(bool(r.get("converged")) for r in rows),"not_converged":sum(not bool(r.get("converged")) for r in rows)},"best_by_anchor":{k:{"K_target":v.get("config",{}).get("K_target"),"M":v.get("config",{}).get("M"),"converged":v.get("converged"),"solve_status":v.get("solve_status"),"residual_linf":v.get("residual_linf"),"residual_l1_nu":v.get("residual_l1_nu"),"tail_ratio_top_10pct":v.get("tail_ratio_top_10pct"),"estimated_strip_width":v.get("estimated_strip_width"),"output_npz":v.get("output_npz"),"record_path":v.get("record_path")} for k,v in best.items()},"elapsed_seconds":time.time()-t0,"records":rows}
    write_json(out/"phase1_seed_summary.json",summary)
    with open(out/"phase1_seed_results.csv","w",encoding="utf-8",newline="") as f:
        fields=["K_target","M","converged","solve_status","residual_linf","residual_l2","residual_l1_nu","weighted_coeff_l1_nu","tail_ratio_top_10pct","estimated_strip_width","estimated_nu_from_decay","max_abs_u","max_abs_r","continuation_success_count","continuation_total_count","elapsed_seconds","output_npz","record_path"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows:
            cfg=r.get("config",{}); w.writerow({"K_target":cfg.get("K_target"),"M":cfg.get("M"),**{k:r.get(k) for k in fields if k not in ("K_target","M")}})
    summary["csv"]=str(out/"phase1_seed_results.csv"); return summary
