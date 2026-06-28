import asyncio
import json
import websockets

async def main():
    url = "wss://stream.binance.com:9443/ws/solusdt@aggTrade"
    async with websockets.connect(url) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(data)

asyncio.run(main())