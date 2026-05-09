from __future__ import annotations

import csv
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from kam_theorem_suite.lower_param.standard_sine_embedding import (
    FourierOps,
    SeedSolveConfig,
    diagnostics,
    newton_at_K,
    save_npz,
)
from kam_theorem_suite.lower_param.lift_alias_audit import coeff, coeff_to_size, samples_from_coeff, write_json, _as_float, GOLDEN_OMEGA


def _clean(o: Any) -> Any:
    if isinstance(o, dict): return {str(k): _clean(v) for k,v in o.items()}
    if isinstance(o, (list, tuple)): return [_clean(v) for v in o]
    if isinstance(o, np.ndarray): return _clean(o.tolist())
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, (np.floating, float)):
        x=float(o); return None if (math.isnan(x) or math.isinf(x)) else x
    if isinstance(o, np.bool_): return bool(o)
    return o


@dataclass(slots=True)
class RefineFromSeedConfig:
    seed_npz: str
    M_out: int
    out_dir: str
    max_newton: int = 24
    gmres_rtol: float = 1e-12
    gmres_atol: float = 1e-14
    gmres_restart: int = 180
    gmres_maxiter: int = 1600
    newton_tol: float = 1e-12
    accept_linf: float = 1e-10
    damping_min: float = 1e-5
    nu: float = 1.003
    force: bool = False


def refine_one(cfg: RefineFromSeedConfig) -> dict[str, Any]:
    t0 = time.time()
    seed = Path(cfg.seed_npz)
    out = Path(cfg.out_dir)
    with np.load(seed, allow_pickle=False) as z:
        K = float(_as_float(z.get('K'), None))
        omega = float(_as_float(z.get('omega'), GOLDEN_OMEGA))
        u = np.asarray(z['u'], dtype=float)
    M_in = int(u.size)
    tag = f"K{K:.10f}".replace('.', 'p') + f"_M{int(cfg.M_out)}_fromM{M_in}"
    npz_path = out / 'embeddings' / f'{tag}.npz'
    rec_path = out / 'records' / f'{tag}.phase4c_refine_from_seed.json'
    if rec_path.exists() and npz_path.exists() and not cfg.force:
        try:
            d = json.loads(rec_path.read_text(encoding='utf-8'))
            d['loaded_from_existing_record'] = True
            return d
        except Exception:
            pass
    c0 = coeff(u)
    u0 = samples_from_coeff(coeff_to_size(c0, int(cfg.M_out)))
    scfg = SeedSolveConfig(
        K_target=float(K),
        M=int(cfg.M_out),
        omega=float(omega),
        continuation_steps=0,
        max_newton=int(cfg.max_newton),
        gmres_rtol=float(cfg.gmres_rtol),
        gmres_atol=float(cfg.gmres_atol),
        gmres_restart=int(cfg.gmres_restart),
        gmres_maxiter=int(cfg.gmres_maxiter),
        newton_tol=float(cfg.newton_tol),
        accept_linf=float(cfg.accept_linf),
        damping_min=float(cfg.damping_min),
        nu=float(cfg.nu),
    )
    op = FourierOps(int(cfg.M_out), float(omega))
    u1, ok, steps = newton_at_K(u0, float(K), scfg, op)
    d = diagnostics(u1, float(K), scfg, op)
    save_npz(npz_path, u1, float(K), scfg, op)
    converged = bool(ok and float(d['residual_linf']) <= float(cfg.accept_linf))
    payload = {
        'schema': 'theorem_iii_trackb_phase4c_refine_from_seed_v1',
        'phase': 'TrackB-Phase4c-refine-high-resolution-seed-from-existing-embedding',
        'diagnostic_only': True,
        'theorem_facing': False,
        'promotion_allowed': False,
        'seed_npz': str(seed),
        'output_npz': str(npz_path),
        'record_path': str(rec_path),
        'K': float(K),
        'omega': float(omega),
        'M_in': M_in,
        'M_out': int(cfg.M_out),
        'converged': converged,
        'newton_ok': bool(ok),
        'residual_linf': float(d['residual_linf']),
        'residual_l2': float(d['residual_l2']),
        'residual_l1_nu': float(d['residual_l1_nu']),
        'weighted_coeff_l1_nu': float(d['weighted_coeff_l1_nu']),
        'tail_ratio_top_10pct': float(d['tail_ratio_top_10pct']),
        'estimated_strip_width': d['estimated_strip_width'],
        'estimated_nu_from_decay': d['estimated_nu_from_decay'],
        'max_abs_u': float(d['max_abs_u']),
        'max_abs_r': float(d['max_abs_r']),
        'newton_iterations_recorded': len(steps),
        'step_records': [asdict(s) for s in steps],
        'config': asdict(cfg),
        'elapsed_seconds': float(time.time() - t0),
    }
    write_json(rec_path, payload)
    return payload


def _task(cfgd: dict[str, Any]) -> dict[str, Any]:
    for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
        os.environ.setdefault(k, '1')
    rec = refine_one(RefineFromSeedConfig(**cfgd))
    return {
        'K': rec.get('K'), 'M_in': rec.get('M_in'), 'M_out': rec.get('M_out'),
        'converged': rec.get('converged'), 'residual_linf': rec.get('residual_linf'),
        'residual_l1_nu': rec.get('residual_l1_nu'), 'tail_ratio_top_10pct': rec.get('tail_ratio_top_10pct'),
        'estimated_strip_width': rec.get('estimated_strip_width'), 'output_npz': rec.get('output_npz'),
        'record_path': rec.get('record_path'),
    }


def run_refinement(*, seed_npzs: Sequence[str], M_outs: Sequence[int], out_dir: str | Path, workers: int = 1, force: bool = False, **kwargs: Any) -> dict[str, Any]:
    t0 = time.time(); out = Path(out_dir); (out/'records').mkdir(parents=True, exist_ok=True); (out/'embeddings').mkdir(parents=True, exist_ok=True)
    tasks = []
    for seed in seed_npzs:
        for M in M_outs:
            tasks.append(asdict(RefineFromSeedConfig(seed_npz=str(seed), M_out=int(M), out_dir=str(out), force=bool(force), **kwargs)))
    rows=[]; nw=max(1,min(int(workers),len(tasks))) if tasks else 1
    if nw == 1:
        for t in tasks: rows.append(_task(t))
    else:
        with ProcessPoolExecutor(max_workers=nw) as ex:
            futs=[ex.submit(_task,t) for t in tasks]
            for fut in as_completed(futs):
                row=fut.result(); rows.append(row); print(f"[phase4c] K={row.get('K')} M={row.get('M_out')} conv={row.get('converged')} res={row.get('residual_linf')}", flush=True)
    rows.sort(key=lambda r:(float(r.get('K') or 0), int(r.get('M_out') or 0)))
    summary={
        'schema':'theorem_iii_trackb_phase4c_refinement_summary_v1',
        'phase':'TrackB-Phase4c-refine-high-resolution-seed-from-existing-embedding',
        'diagnostic_only':True,'theorem_facing':False,'promotion_allowed':False,
        'status':'phase4c-refinement-complete' if rows else 'no-tasks',
        'parameters': {'seed_count':len(seed_npzs),'M_outs':[int(x) for x in M_outs], 'workers_requested':workers, 'workers_used':nw, **kwargs},
        'counts': {'tasks':len(tasks),'completed_records':len(rows),'converged':sum(bool(r.get('converged')) for r in rows),'not_converged':sum(not bool(r.get('converged')) for r in rows)},
        'records':rows,
        'elapsed_seconds':float(time.time()-t0),
    }
    write_json(out/'phase4c_refinement_summary.json', summary)
    csv_path=out/'phase4c_refinement_results.csv'
    fields=['K','M_in','M_out','converged','residual_linf','residual_l1_nu','tail_ratio_top_10pct','estimated_strip_width','output_npz','record_path']
    with csv_path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); [w.writerow({k:r.get(k) for k in fields}) for r in rows]
    summary['csv']=str(csv_path)
    return summary
