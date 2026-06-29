import pandas as pd
import requests


SYMBOL = "SOLUSDT"
INTERVAL = "5m"
TOTAL_CANDLES = 15005
LIMIT = 1500
URL = "https://fapi.binance.com/fapi/v1/klines"


def fetch_candles(symbol: str, interval: str, total_candles: int, limit: int) -> pd.DataFrame:
    all_data = []
    end_time = None
    remaining = total_candles

    print(f"Collecting {total_candles} candles of {symbol} ({interval}) from Binance API...")

    while remaining > 0:
        current_limit = min(limit, remaining)
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": current_limit,
            "endTime": end_time
        }
        
        response = requests.get(URL, params=params)
        response.raise_for_status()
        data = response.json()
        
            
        all_data.extend(data)
        remaining -= len(data)
        

        end_time = data[0][0] - 1 
        
        progress = ((total_candles - remaining) / total_candles) * 100
        print(f"{progress:.2f}% complete")

    df = pd.DataFrame([row[:6] for row in all_data], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df


def analyze_transitions(df: pd.DataFrame):

    df["state"] = "down"
    df.loc[df["close"] > df["open"], "state"] = "up"
    df["previous_state"] = df['state'].shift(1)
    
    df_clean = df.dropna().copy()
    
    transitions = df_clean.groupby(['previous_state', 'state']).size().to_dict()
    
    uu = transitions.get(('up', 'up'), 0)
    ud = transitions.get(('up', 'down'), 0)
    du = transitions.get(('down', 'up'), 0)
    dd = transitions.get(('down', 'down'), 0)
    total = len(df_clean)

    print(f"\nUU: {uu}, DD: {dd}, DU: {du}, UD: {ud}")
    print(f"UU_chance: {uu/total*100:.2f}%, DD_chance: {dd/total*100:.2f}%, DU_chance: {du/total*100:.2f}%, UD_chance: {ud/total*100:.2f}%")

    latest_state = df_clean.iloc[-1]["state"]
    print(f"\nLatest observed state: {latest_state.upper()}")

    if latest_state == "up":
        prediction_u = (uu / (uu + ud)) * 100
        prediction_d = (ud / (uu + ud)) * 100
    else:
        prediction_u = (du / (du + dd)) * 100
        prediction_d = (dd / (du + dd)) * 100

    print(f"Prediction for next state -> Up: {prediction_u:.2f}%, Down: {prediction_d:.2f}%")


if __name__ == "__main__":
    historical_df = fetch_candles(SYMBOL, INTERVAL, TOTAL_CANDLES, LIMIT)
    
    analyze_transitions(historical_df)