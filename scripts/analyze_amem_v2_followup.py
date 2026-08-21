"""Paper-ready paired analysis for the matched A-MEM evolution follow-up."""
import argparse, json, pathlib
from harness.schema import read_jsonl
from harness.stats import bootstrap_metric
import scripts.sensitivity_analysis as sens

def ivs(table): return {k: vars(v) for k, v in table.items()}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("c3"); ap.add_argument("c4"); ap.add_argument("--out",type=pathlib.Path,required=True)
    args=ap.parse_args(); rows={"C3E0":read_jsonl(args.c3),"C4E1":read_jsonl(args.c4)}
    assert all(len(v)==1800 for v in rows.values())
    ids={r["probe_id"] for r in rows["C3E0"]}; cmap,unit=sens.cluster_map_for(ids); pair=(("C4E1","C3E0"),)
    out={"n_rows_per_arm":1800,"n_clusters":len(set(cmap.values())) if cmap else len(ids),"cluster_unit":unit,"n_boot":2000,"seed":0,"contrast":"C4E1-C3E0"}
    for metric in ("harm","refusal","derailment"):
        rates,diffs=bootstrap_metric(rows,"D",metric,comparisons=pair,n_boot=2000,seed=0,cluster_map=cmap); out[metric]={"rates":ivs(rates),"contrast":ivs(diffs)}
    sens.CONTRASTS=pair
    for name,classifier,tally in (("strict_floor",sens.classify_strict_floor,sens.harm_tally),("composite",sens.classify,sens.composite_tally)):
        rates,diffs,n,u=sens.contrast_intervals(rows,"D",classifier,tally,n_boot=2000,seed=0); out[name]={"rates":rates,"contrast":ivs(diffs),"n_clusters":n,"cluster_unit":u}
    args.out.mkdir(parents=True,exist_ok=True); (args.out/"results.json").write_text(json.dumps(out,indent=2)+"\n")
    lines=["C4E1 - C3E0; 2,000 paired probe-clustered draws; BCa 95%"]
    for metric in ("harm","refusal","derailment"):
        x=out[metric]; d=x["contrast"]["C4E1-C3E0"]; lines.append(f"{metric}: C3E0={x['rates']['C3E0']['point']:.3%} C4E1={x['rates']['C4E1']['point']:.3%} diff={d['point']:+.3%} BCa=[{d['bca_lo']:+.3%},{d['bca_hi']:+.3%}]")
    for name in ("strict_floor","composite"):
        x=out[name]; d=x["contrast"]["C4E1-C3E0"]; lines.append(f"{name}: C3E0={x['rates']['C3E0']:.3%} C4E1={x['rates']['C4E1']:.3%} diff={d['point']:+.3%} BCa=[{d['bca_lo']:+.3%},{d['bca_hi']:+.3%}]")
    (args.out/"results.txt").write_text("\n".join(lines)+"\n"); print("\n".join(lines))
if __name__=="__main__": main()
