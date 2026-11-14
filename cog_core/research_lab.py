"""Offline, illustrative close-price research. No trading or exchange access."""
import csv
import math
from pathlib import Path

def backtest(path,window=10,fee_bps=10.0):
    if not isinstance(window,int) or not 2<=window<=1000 or not math.isfinite(fee_bps) or not 0<=fee_bps<=1000:
        raise ValueError("Invalid window or fee.")
    path=Path(path)
    if path.stat().st_size>16*1024*1024:
        raise ValueError("CSV exceeds 16 MiB.")
    prices=[]
    with path.open(encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle)
        if not reader.fieldnames or "close" not in reader.fieldnames:
            raise ValueError("CSV requires a close column in chronological order.")
        for row in reader:
            price=float(row["close"])
            if not math.isfinite(price) or not 0<price<=1e12:
                raise ValueError("Invalid close price.")
            prices.append(price)
            if len(prices)>100000:
                raise ValueError("Too many rows.")
    if len(prices)<=window:
        raise ValueError("Need more rows than window.")
    equity=1.0
    peak=1.0
    drawdown=0.0
    held=0
    switches=0
    cost=fee_bps/10000
    # Signal at prior close; earn only the following close-to-close return.
    # Illustrative fill assumption, not an executable market strategy.
    for i in range(window,len(prices)):
        signal=int(prices[i-1]>sum(prices[i-window:i])/window)
        if signal!=held:
            equity*=1-cost
            switches+=1
        equity*=1+signal*(prices[i]/prices[i-1]-1)
        if not math.isfinite(equity):
            raise ValueError("Numerical overflow.")
        held=signal
        peak=max(peak,equity)
        drawdown=max(drawdown,1-equity/peak)
    if held:
        equity*=1-cost
        switches+=1
        drawdown=max(drawdown,1-equity/peak)
    return {"rows":len(prices),"window":window,"fee_bps":fee_bps,"return_pct":100*(equity-1),
            "max_drawdown_pct":100*drawdown,"position_changes":switches,
            "notice":"Offline illustration; assumes close-price fills, no spread or slippage beyond fees. Not a binary event-contract backtest or live trading."}
