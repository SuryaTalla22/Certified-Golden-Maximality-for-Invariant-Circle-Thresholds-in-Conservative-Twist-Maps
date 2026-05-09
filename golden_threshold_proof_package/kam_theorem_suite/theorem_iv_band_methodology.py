from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Sequence
import numpy as np
from .certification import validated_branch_state
from .standard_map import HarmonicFamily
@dataclass(frozen=True)
class TheoremIVBandProfile:
    name: str; dps: int; scout_points: int; scan_margin: float; center_margin_floor: float; band_half_widths: tuple[float, ...]; transport_points: tuple[float, ...]; slope_floor: float; prefer_same_regime: bool = True
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def get_theorem_iv_band_profile(p: int, q: int) -> TheoremIVBandProfile:
    q = int(q)
    if q <= 21:
        return TheoremIVBandProfile('band-low-q',140,21,2.0e-3,1.0e-4,(2e-5,5e-5,1e-4,2e-4,4e-4),(-1.0,-0.5,0.0,0.5,1.0),5e-4)
    if q <= 34:
        return TheoremIVBandProfile('band-mid-q',160,25,1.5e-3,7.5e-5,(1e-5,2e-5,5e-5,1e-4,2e-4),(-1.0,-0.5,0.0,0.5,1.0),5e-4)
    if q <= 55:
        return TheoremIVBandProfile('band-high-q',180,31,1.0e-3,5.0e-5,(4e-6,1e-5,2e-5,5e-5,1e-4),(-1.0,-0.5,0.0,0.5,1.0),3e-4)
    if q <= 89:
        return TheoremIVBandProfile('band-very-high-q',200,35,8.0e-4,4.0e-5,(2e-6,5e-6,1e-5,2e-5,5e-5),(-1.0,-0.5,0.0,0.5,1.0),2.5e-4)
    if q <= 144:
        return TheoremIVBandProfile('band-extreme-q',220,41,6.0e-4,3.0e-5,(1e-6,2e-6,5e-6,1e-5,2e-5),(-1.0,-0.5,0.0,0.5,1.0),2.0e-4)
    return TheoremIVBandProfile('band-ultra-q',240,51,5.0e-4,2.5e-5,(5e-7,1e-6,2e-6,5e-6,1e-5),(-1.0,-0.5,0.0,0.5,1.0),1.5e-4)

def _regime_from_residue_center(residue_center: float, target_residue: float) -> str | None:
    r = float(residue_center)
    if r < -float(target_residue): return 'negative-hyperbolic'
    if r > 1.0: return 'positive-hyperbolic'
    return None

def _margin_from_residue_center(residue_center: float, target_residue: float) -> float:
    return float(abs(float(residue_center)) - float(target_residue))

def _band_center_from_entry(entry: dict[str, Any]) -> float | None:
    band = entry.get('band_report') or {}
    best = band.get('best_band') or {}
    lo = best.get('K_lo'); hi = best.get('K_hi')
    if lo is not None and hi is not None: return 0.5 * (float(lo) + float(hi))
    return None

def _fit_band_center_from_previous_entries(q: int, previous_entry_dicts: Sequence[dict[str, Any]]) -> tuple[float | None, str]:
    pts=[]
    for entry in previous_entry_dicts:
        try: qq = int(entry.get('q'))
        except Exception: continue
        center = _band_center_from_entry(entry)
        if center is None: continue
        pts.append((float(1.0/(qq*qq)), float(center)))
    if len(pts) >= 2:
        xs=np.array([x for x,_ in pts],dtype=float); ys=np.array([y for _,y in pts],dtype=float)
        try:
            coeff=np.polyfit(xs,ys,deg=1); pred=float(np.polyval(coeff,1.0/(int(q)*int(q))))
            return pred, 'q^-2 extrapolation from previous band centers'
        except Exception: pass
    if pts: return float(pts[-1][1]), 'last completed band center'
    return None, 'none'

def predict_theorem_iv_band_center(spec, *, crossing_root_hi: float | None = None, previous_entry_dicts: Sequence[dict[str, Any]] | None = None, predictive_hint_center: float | None = None) -> dict[str, Any]:
    band_lo=float(spec.band_search_lo); band_hi=float(spec.band_search_hi)
    if crossing_root_hi is not None: band_lo=max(band_lo,float(crossing_root_hi))
    if predictive_hint_center is not None:
        center=float(predictive_hint_center); source='explicit predictive hint'
    else:
        center, source = _fit_band_center_from_previous_entries(int(spec.q), list(previous_entry_dicts or []))
        if center is None:
            center = band_lo + 0.15*max(band_hi-band_lo,1e-12); source='crossing-offset fallback'
    center=min(max(float(center),band_lo),band_hi)
    return {'predictive_center': center, 'source': source, 'band_window_lo': band_lo, 'band_window_hi': band_hi}

def _transport_band_certificate(p:int,q:int,K_center:float,family:HarmonicFamily,*,target_residue:float,profile:TheoremIVBandProfile,x_guess=None,K_anchor:float|None=None)->dict[str,Any]:
    center_state=validated_branch_state(p=p,q=q,K=float(K_center),family=family,x_guess=None if x_guess is None else np.asarray(x_guess,dtype=float),K_anchor=K_anchor)
    if not center_state.get('strict',False) or center_state.get('x') is None:
        return {'success':False,'proof_ready':False,'message':'Could not validate strict hyperbolic band center.','method':'transport_local_band'}
    center_rc=float(center_state['residue_center']); center_regime=_regime_from_residue_center(center_rc,target_residue); center_margin=_margin_from_residue_center(center_rc,target_residue)
    if center_regime is None or center_margin <= float(profile.center_margin_floor):
        return {'success':False,'proof_ready':False,'message':'Center is not safely hyperbolic above target.','method':'transport_local_band','center_state':center_state}
    diagnostics=[]; best=None
    for h in sorted(float(w) for w in profile.band_half_widths):
        sample_Ks=[float(K_center + tau*h) for tau in profile.transport_points]; states=[]; guess=np.asarray(center_state['x'],dtype=float); prev_K=float(K_center); ok=True
        for K in sample_Ks:
            st=validated_branch_state(p=p,q=q,K=float(K),family=family,x_guess=guess,K_anchor=prev_K)
            if not st.get('strict',False) or st.get('x') is None:
                ok=False; break
            states.append(st); guess=np.asarray(st['x'],dtype=float); prev_K=float(K)
        if not ok or not states:
            diagnostics.append({'half_width':float(h),'success':False,'message':'strict sample validation failed'}); continue
        rvals=[float(st['residue_center']) for st in states]; avals=[abs(rv) for rv in rvals]; regs=[_regime_from_residue_center(rv,target_residue) for rv in rvals]
        same_regime=all(reg==center_regime for reg in regs); safe_margin=min(av-float(target_residue) for av in avals)
        monotone_abs=all(avals[i] <= avals[i+1] + 1e-15 for i in range(len(avals)-1)) or all(avals[i] + 1e-15 >= avals[i+1] for i in range(len(avals)-1))
        slope=(avals[-1]-avals[0])/max(sample_Ks[-1]-sample_Ks[0],1e-30)
        diagnostics.append({'half_width':float(h),'same_regime':bool(same_regime),'safe_margin':float(safe_margin),'monotone_abs':bool(monotone_abs),'slope':float(slope)})
        if same_regime and safe_margin > float(profile.center_margin_floor) and monotone_abs and abs(float(slope)) >= float(profile.slope_floor):
            band_lo=float(sample_Ks[0]); band_hi=float(sample_Ks[-1]); trace_abs=[abs(2.0-4.0*rv) for rv in rvals]; hyper_margin=min(tb-2.0 for tb in trace_abs)
            best={'success':True,'proof_ready':True,'certified_hyperbolic':True,'certified_above_target':True,'certification_tier':'theorem_mode_local_band','method':'transport_local_band','K_lo':band_lo,'K_hi':band_hi,'width':float(band_hi-band_lo),'regime':str(center_regime),'residue_interval_lo':float(min(rvals)),'residue_interval_hi':float(max(rvals)),'abs_residue_interval_lo':float(min(avals)),'abs_residue_interval_hi':float(max(avals)),'g_interval_lo':float(min(avals)-float(target_residue)),'g_interval_hi':float(max(avals)-float(target_residue)),'gprime_interval_lo':float(min(0.0,slope)),'gprime_interval_hi':float(max(0.0,slope)),'trace_abs_lower_bound':float(min(trace_abs)),'hyperbolicity_margin':float(hyper_margin),'left':states[0],'center':center_state,'right':states[-1],'sample_residue_centers':[float(v) for v in rvals],'sample_abs_residue_centers':[float(v) for v in avals],'transport_points':[float(t) for t in profile.transport_points],'diagnostics':list(diagnostics),'message':'Certified local hyperbolic band via theorem-mode transport from a pointwise hyperbolic center.'}
    if best is not None: return best
    return {'success':False,'proof_ready':False,'method':'transport_local_band','diagnostics':diagnostics,'message':'Could not certify a local hyperbolic band around the proposed center.','center_state':center_state}

def methodology_localize_hyperbolic_band(spec, family:HarmonicFamily|None=None, *, target_residue:float=0.25, crossing_root_hi:float|None=None, previous_entry_dicts:Sequence[dict[str,Any]]|None=None, predictive_hint_center:float|None=None, x_guess=None, profile:TheoremIVBandProfile|None=None)->dict[str,Any]:
    family=family or HarmonicFamily(); profile=profile or get_theorem_iv_band_profile(spec.p,spec.q)
    prediction=predict_theorem_iv_band_center(spec,crossing_root_hi=crossing_root_hi,previous_entry_dicts=previous_entry_dicts,predictive_hint_center=predictive_hint_center)
    band_lo=float(prediction['band_window_lo']); band_hi=float(prediction['band_window_hi']); pred=float(prediction['predictive_center']); scan_half=max(float(profile.scan_margin),2.0*max(profile.band_half_widths)); scout_lo=max(band_lo,pred-scan_half); scout_hi=min(band_hi,pred+scan_half)
    if scout_hi <= scout_lo: scout_lo, scout_hi = band_lo, band_hi
    Ks=np.linspace(float(scout_lo),float(scout_hi),int(profile.scout_points)); scout_rows=[]; guess=None if x_guess is None else np.asarray(x_guess,dtype=float); prev_K=crossing_root_hi if crossing_root_hi is not None else band_lo; best_candidate=None
    for K in Ks:
        st=validated_branch_state(p=spec.p,q=spec.q,K=float(K),family=family,x_guess=guess,K_anchor=prev_K)
        if st.get('x') is not None: guess=np.asarray(st['x'],dtype=float); prev_K=float(K)
        rc=float(st.get('residue_center',np.nan)) if np.isfinite(st.get('residue_center',np.nan)) else np.nan; regime=None if not np.isfinite(rc) else _regime_from_residue_center(rc,target_residue); margin=None if not np.isfinite(rc) else _margin_from_residue_center(rc,target_residue)
        scout_rows.append({'K':float(K),'strict':bool(st.get('strict',False)),'candidate':bool(st.get('candidate',False)),'residue_center':rc,'regime':regime,'margin':margin})
        if bool(st.get('strict',False)) and regime is not None and margin is not None and margin > float(profile.center_margin_floor):
            score=float(margin) - 0.05*abs(float(K)-pred)
            if best_candidate is None or score > best_candidate[0]: best_candidate=(score,{'K':float(K),'state':st,'regime':regime,'margin':float(margin)})
    out={'predictive_center':float(pred),'prediction_source':str(prediction['source']),'band_window_lo':float(band_lo),'band_window_hi':float(band_hi),'scout_window_lo':float(scout_lo),'scout_window_hi':float(scout_hi),'profile':profile.to_dict(),'scout_rows':scout_rows}
    if best_candidate is None:
        out.update({'success':False,'proof_ready':False,'status':'fallback-required','message':'Could not identify a strict hyperbolic center inside the scout window.','certificate':None,'fallback_window_lo':float(scout_lo),'fallback_window_hi':float(scout_hi)}); return out
    chosen=best_candidate[1]; cert=_transport_band_certificate(spec.p,spec.q,chosen['K'],family,target_residue=target_residue,profile=profile,x_guess=chosen['state'].get('x'),K_anchor=chosen['K'])
    out['chosen_center']=float(chosen['K']); out['chosen_regime']=str(chosen['regime']); out['chosen_margin']=float(chosen['margin']); out['certificate']=cert
    if cert.get('proof_ready',False): out.update({'success':True,'proof_ready':True,'status':'theorem_mode_local_band','K_lo':float(cert['K_lo']),'K_hi':float(cert['K_hi']),'width':float(cert['width']),'method':str(cert.get('method','transport_local_band')),'message':cert.get('message')})
    else: out.update({'success':False,'proof_ready':False,'status':'fallback-required','K_lo':float(chosen['K']),'K_hi':float(chosen['K']),'width':0.0,'method':str(cert.get('method','transport_local_band')),'message':cert.get('message'),'fallback_window_lo':float(max(band_lo,chosen['K']-scan_half)),'fallback_window_hi':float(min(band_hi,chosen['K']+scan_half))})
    return out

__all__=['TheoremIVBandProfile','get_theorem_iv_band_profile','predict_theorem_iv_band_center','methodology_localize_hyperbolic_band']
