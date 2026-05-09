from __future__ import annotations
import json, math, os, time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
import numpy as np
from scipy.sparse.linalg import LinearOperator, gmres

GOLDEN_OMEGA = (math.sqrt(5.0)-1.0)/2.0
TWOPI = 2.0*math.pi

def _clean(o: Any) -> Any:
    if isinstance(o, dict): return {str(k): _clean(v) for k,v in o.items()}
    if isinstance(o, (list, tuple)): return [_clean(v) for v in o]
    if isinstance(o, np.ndarray): return _clean(o.tolist())
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, (np.floating, float)):
        x=float(o); return None if (math.isnan(x) or math.isinf(x)) else x
    if isinstance(o, np.bool_): return bool(o)
    return o

def write_json(path: str|Path, payload: dict[str,Any]) -> Path:
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(_clean(payload), indent=2, sort_keys=True)+"\n", encoding="utf-8")
    os.replace(tmp, path); return path

@dataclass(slots=True)
class SeedSolveConfig:
    K_target: float
    M: int = 512
    omega: float = GOLDEN_OMEGA
    continuation_steps: int = 36
    max_newton: int = 16
    gmres_rtol: float = 1e-11
    gmres_atol: float = 1e-13
    gmres_restart: int = 80
    gmres_maxiter: int = 600
    newton_tol: float = 1e-11
    accept_linf: float = 1e-8
    damping_min: float = 1e-4
    nu: float = 1.015
    phase_pin_index: int = 0
    verbose: bool = False

@dataclass(slots=True)
class NewtonStepRecord:
    K: float; iteration: int; residual_linf: float; residual_l2: float
    gmres_info: int|None; correction_linf: float|None; damping: float|None; accepted: bool

@dataclass(slots=True)
class SeedSolveResult:
    config: SeedSolveConfig
    converged: bool
    solve_status: str
    residual_linf: float
    residual_l2: float
    residual_l1_nu: float
    weighted_coeff_l1_nu: float
    tail_ratio_top_10pct: float
    estimated_strip_width: float|None
    estimated_nu_from_decay: float|None
    max_abs_u: float
    max_abs_r: float
    mean_u: float
    phase_pin_value: float
    continuation_success_count: int
    continuation_total_count: int
    elapsed_seconds: float
    step_records: list[NewtonStepRecord] = field(default_factory=list)
    output_npz: str|None = None
    def to_dict(self) -> dict[str,Any]:
        d=asdict(self); d.update(schema="theorem_iii_trackb_phase1_seed_v1", diagnostic_only=True, theorem_facing=False, promotion_allowed=False); return d

class FourierOps:
    def __init__(self, M:int, omega:float):
        if M < 8: raise ValueError("M must be >= 8")
        if M & (M-1): raise ValueError(f"M={M} is not a power of two")
        self.M=int(M); self.omega=float(omega)
        self.theta=np.arange(M,dtype=float)/float(M)
        self.freq=np.fft.fftfreq(M,d=1.0/M); self.abs_freq=np.abs(self.freq)
        self.sp=np.exp(1j*TWOPI*self.freq*self.omega); self.sm=np.conjugate(self.sp)
    def shift(self,u:np.ndarray, sign:int)->np.ndarray:
        return np.fft.ifft(np.fft.fft(np.asarray(u,dtype=float))*(self.sp if sign>=0 else self.sm)).real
    def coeffs(self,u:np.ndarray)->np.ndarray:
        return np.fft.fft(np.asarray(u,dtype=float))/float(self.M)
    def weighted_l1(self,u:np.ndarray,nu:float)->float:
        return float(np.sum(np.abs(self.coeffs(u))*np.exp(np.log(float(nu))*self.abs_freq)))

def residual(u:np.ndarray,K:float,op:FourierOps)->np.ndarray:
    x=op.theta+np.asarray(u,dtype=float)
    return op.shift(u,+1)-2*u+op.shift(u,-1)-(float(K)/TWOPI)*np.sin(TWOPI*x)

def solve_residual(u:np.ndarray,K:float,op:FourierOps,pin:int=0)->np.ndarray:
    r=residual(u,K,op).copy(); r[int(pin)%op.M]=u[int(pin)%op.M]; return r

def linop(u:np.ndarray,K:float,op:FourierOps,pin:int=0)->LinearOperator:
    x=op.theta+u; diag=-2.0-float(K)*np.cos(TWOPI*x); idx=int(pin)%op.M
    def mv(d):
        d=np.asarray(d,dtype=float); y=op.shift(d,+1)+op.shift(d,-1)+diag*d; y[idx]=d[idx]; return y
    return LinearOperator((op.M,op.M), matvec=mv, dtype=float)

def _gmres(A,b,cfg):
    try:
        return gmres(A,b,rtol=cfg.gmres_rtol,atol=cfg.gmres_atol,restart=cfg.gmres_restart,maxiter=cfg.gmres_maxiter)
    except TypeError:
        return gmres(A,b,tol=cfg.gmres_rtol,restart=cfg.gmres_restart,maxiter=cfg.gmres_maxiter)

def _norms(v):
    return float(np.max(np.abs(v))), float(np.linalg.norm(v)/math.sqrt(v.size))

def newton_at_K(u0,K,cfg,op):
    u=np.asarray(u0,dtype=float).copy(); rec=[]; prev=math.inf
    for it in range(cfg.max_newton):
        sr=solve_residual(u,K,op,cfg.phase_pin_index); linf,l2=_norms(sr)
        if linf <= cfg.newton_tol:
            rec.append(NewtonStepRecord(K,it,linf,l2,None,0.0,0.0,True)); return u, True, rec
        delta,info=_gmres(linop(u,K,op,cfg.phase_pin_index), -sr, cfg); delta=np.asarray(delta,dtype=float)
        cl=float(np.max(np.abs(delta))); alpha=1.0; accepted=False; chosen=None
        while alpha >= cfg.damping_min:
            trial=u+alpha*delta; tn=float(np.max(np.abs(solve_residual(trial,K,op,cfg.phase_pin_index))))
            if tn < linf or tn < prev:
                u=trial; prev=tn; accepted=True; chosen=alpha; break
            alpha *= 0.5
        rec.append(NewtonStepRecord(K,it,linf,l2,int(info),cl,chosen,accepted))
        if not accepted: return u, False, rec
        if cl*float(chosen or 0.0) <= max(1e-14,0.1*cfg.newton_tol):
            if float(np.max(np.abs(solve_residual(u,K,op,cfg.phase_pin_index)))) <= 10*cfg.newton_tol:
                return u, True, rec
    return u, float(np.max(np.abs(solve_residual(u,K,op,cfg.phase_pin_index)))) <= cfg.accept_linf, rec

def continuation_schedule(Ktarget:float, steps:int)->list[float]:
    if Ktarget <= 0: return [float(Ktarget)]
    s=np.linspace(0,1,max(1,int(steps))+1)[1:]
    vals=float(Ktarget)*(1-(1-s)**1.6); vals[-1]=float(Ktarget)
    out=[]
    for v in vals:
        if not out or float(v)>out[-1]+1e-14: out.append(float(v))
    return out

def diagnostics(u,K,cfg,op):
    res=residual(u,K,op); linf,l2=_norms(res)
    coeff=np.abs(op.coeffs(u)); af=op.abs_freq; total=float(np.sum(coeff))
    top=float(np.percentile(af,90)); tail=float(np.sum(coeff[af>=top])/total) if total>0 else 0.0
    strip=None; nud=None; mask=(af>=4)&(af<=np.max(af)*0.65)&(coeff>max(np.max(coeff)*1e-14,1e-300))
    if int(np.sum(mask))>=8:
        slope,_=np.polyfit(af[mask],np.log(coeff[mask]),1)
        if slope<0 and math.isfinite(float(slope)):
            strip=float(-slope); nud=float(math.exp(strip)) if strip<50 else None
    x=op.theta+u; r=x-(op.theta-cfg.omega+op.shift(u,-1))
    return dict(residual_linf=linf,residual_l2=l2,residual_l1_nu=op.weighted_l1(res,cfg.nu),weighted_coeff_l1_nu=op.weighted_l1(u,cfg.nu),tail_ratio_top_10pct=tail,estimated_strip_width=strip,estimated_nu_from_decay=nud,max_abs_u=float(np.max(np.abs(u))),max_abs_r=float(np.max(np.abs(r))),mean_u=float(np.mean(u)),phase_pin_value=float(u[int(cfg.phase_pin_index)%cfg.M]))

def save_npz(path,u,K,cfg,op):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    x=op.theta+u; r=x-(op.theta-cfg.omega+op.shift(u,-1)); res=residual(u,K,op)
    np.savez_compressed(path,schema="theorem_iii_trackb_phase1_embedding_npz_v1",diagnostic_only=True,theorem_facing=False,K=float(K),M=int(cfg.M),omega=float(cfg.omega),theta=op.theta,u=u,x=x,r=r,residual=res,u_coeff=op.coeffs(u),residual_coeff=op.coeffs(res),freq=op.freq)
    return path

def solve_anchor_with_continuation(cfg:SeedSolveConfig, *, out_npz:str|Path|None=None, initial_u:np.ndarray|None=None)->SeedSolveResult:
    t0=time.time(); op=FourierOps(cfg.M,cfg.omega); u=np.zeros(cfg.M) if initial_u is None else np.asarray(initial_u,dtype=float).copy()
    allrec=[]; okcount=0; sched=continuation_schedule(cfg.K_target,cfg.continuation_steps); status="not-started"
    for K in sched:
        u,ok,rec=newton_at_K(u,K,cfg,op); allrec.extend(rec)
        if ok: okcount+=1; status="continuing"
        else: status=f"failed-at-K={K:.16g}"; break
    d=diagnostics(u,cfg.K_target,cfg,op); conv=bool(okcount==len(sched) and float(d["residual_linf"])<=cfg.accept_linf)
    if conv: status="converged-target"
    elif okcount==len(sched): status="completed-continuation-but-residual-above-acceptance"
    npz=None
    if out_npz is not None: npz=str(save_npz(out_npz,u,cfg.K_target,cfg,op))
    return SeedSolveResult(config=cfg,converged=conv,solve_status=status,residual_linf=float(d["residual_linf"]),residual_l2=float(d["residual_l2"]),residual_l1_nu=float(d["residual_l1_nu"]),weighted_coeff_l1_nu=float(d["weighted_coeff_l1_nu"]),tail_ratio_top_10pct=float(d["tail_ratio_top_10pct"]),estimated_strip_width=d["estimated_strip_width"],estimated_nu_from_decay=d["estimated_nu_from_decay"],max_abs_u=float(d["max_abs_u"]),max_abs_r=float(d["max_abs_r"]),mean_u=float(d["mean_u"]),phase_pin_value=float(d["phase_pin_value"]),continuation_success_count=okcount,continuation_total_count=len(sched),elapsed_seconds=float(time.time()-t0),step_records=allrec,output_npz=npz)
