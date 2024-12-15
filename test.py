import asyncio
import websockets
import json
import cv2
import numpy as np
import pyaudio  # 导入 PyAudio

async def main():
    async with websockets.connect('ws://localhost:8765') as websocket:
        await websocket.send(json.dumps({"action": "mic","mode": "open"}))
        data=await websocket.recv()
        if (json.loads(data))["status"]=="success":
            print("Mic opened.")
            p=pyaudio.PyAudio()
            mic=p.open(format=pyaudio.paInt16,channels=1,rate=44100,output=True,frames_per_buffer=1024)

        for _ in range(1000):
            audio_data = await websocket.recv()
            if isinstance(audio_data, str):
                audio_data = audio_data.encode('latin1')
            mic.write(audio_data)

        await websocket.send(json.dumps({"action": "mic","mode": "close"}))
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                break
            except json.JSONDecodeError:
                continue
        if data["status"]=="success":
            print("Mic closed.")
            mic.stop_stream()
            mic.close()
            p.terminate()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())