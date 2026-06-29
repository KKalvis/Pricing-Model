import pandas as pd
import requests


SYMBOL = "SOLUSDT"
INTERVAL = "5m"
TOTAL_CANDLES = 150000
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



def analyze_transitions(df: pd.DataFrame, past_candles: int = 2):
    df["state"] = "down"
    df.loc[df["close"] > df["open"], "state"] = "up"
    df["previous_state"] = df['state'].shift(1)

    

    history_cols = []

    for i in range(past_candles, 0, -1):
        df[f'state_minus_{i}'] = df['state'].shift(i)
        history_cols.append(f'state_minus_{i}')

    df_clean = df.dropna().copy()
    df_clean["history"] = df_clean[history_cols].agg(''.join, axis=1)


    latest_history = "".join(df_clean["state"].iloc[-past_candles:].tolist())
    transitions = df_clean.groupby(['history', 'state']).size().to_dict()

    if transitions.get((latest_history, 'up'), 0) + transitions.get((latest_history, 'down'), 0) == 0:
        print(f"\nNo historical occurrences of pattern. Try lowering the number of past candles, or increasing the dataset size: {latest_history}. Unable to make a prediction.")
        return

    prediction_u = transitions.get((latest_history, 'up'), 0) / (transitions.get((latest_history, 'up'), 0) + transitions.get((latest_history, 'down'), 0)) * 100
    prediction_d = transitions.get((latest_history, 'down'), 0) / (transitions.get((latest_history, 'up'), 0) + transitions.get((latest_history, 'down'), 0)) * 100

    print(f"Prediction for next state -> Up: {prediction_u:.2f}%, Down: {prediction_d:.2f}%")



if __name__ == "__main__":
    historical_df = fetch_candles(SYMBOL, INTERVAL, TOTAL_CANDLES, LIMIT)
    
    analyze_transitions(historical_df, past_candles=3)
    