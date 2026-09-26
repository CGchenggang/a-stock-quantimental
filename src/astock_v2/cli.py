import argparse
from pathlib import Path
import pandas as pd
from .backtest.engine import evaluate_signals

def main():
    p=argparse.ArgumentParser("astock-v2")
    sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("init")
    d=sub.add_parser("demo"); d.add_argument("symbol")
    b=sub.add_parser("backtest"); b.add_argument("--csv",required=True)
    a=p.parse_args()
    if a.cmd=="init":
        for x in ["data/raw","data/cache","data/pit","workspace/runs","workspace/models","workspace/reports"]:
            Path(x).mkdir(parents=True,exist_ok=True)
        print("initialized")
    elif a.cmd=="demo":
        print({"symbol":a.symbol,"status":"research-packet-scaffold-ready"})
    else:
        df=pd.read_csv(a.csv)
        print(evaluate_signals(df))

if __name__=="__main__":
    main()
