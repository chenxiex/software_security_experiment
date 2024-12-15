import asyncio
import websockets
import json
import cv2
import numpy as np
import pyaudio  # 导入 PyAudio

# Envs
port=8765
host="localhost"

connected_client = None
mic_open=False
mic=None
camera_open=False

def disp_camera(response):
    frame=response
    if isinstance(frame, str):
        frame = frame.encode('latin1')  # 将字符串转换为字节
    np_arr = np.frombuffer(frame, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        print("Warning: Failed to decode image")
        return
    cv2.imshow("Camera Feed", img)

def play_mic(response):
    global mic_open
    global mic
    # 接收麦克风数据并播放
    audio_data = response
    if isinstance(audio_data, str):
        audio_data = audio_data.encode('latin1')
    mic.write(audio_data)

async def handler(websocket):
    global connected_client
    global camera_open
    global mic_open
    global mic
    try:
        if connected_client and connected_client.state == websockets.protocol.State.CLOSED:
            connected_client = None

        if connected_client:
            response = {
                "status": "error",
                "message": "Another client is already connected."
            }
            await websocket.send(json.dumps(response))
            return

        connected_client = websocket
        response = {
            "status": "success",
            "message": "Connection established."
        }
        await websocket.send(json.dumps(response))
        print("Client connected.")

        async for message in websocket:
            try:
                data = json.loads(message)
                if data['action'] == 'ping':
                    response = {
                        "status": "success",
                    }
                    await websocket.send(json.dumps(response))
                elif data['action'] == 'camera':
                    if data['mode'] == 'open':
                        if not camera_open:
                            camera_open = True
                        cv2.namedWindow("Camera Feed", cv2.WINDOW_AUTOSIZE)
                        response = {
                            "status": "success",
                            "message": "Camera opened."
                        }
                        await websocket.send(json.dumps(response))
                    elif data['mode'] == 'close':
                        camera_open = False
                        cv2.destroyAllWindows()
                        response = {
                            "status": "success",
                            "message": "Camera closed."
                        }
                        await websocket.send(json.dumps(response))
                elif data['action'] == 'mic':
                    if data['mode'] == 'open':
                        if not mic_open:
                            mic_open = True
                            p = pyaudio.PyAudio()
                            mic = p.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True)
                        response = {
                            "status": "success",
                            "message": "Mic opened."
                        }
                        await websocket.send(json.dumps(response))
                    elif data['mode'] == 'close':
                        mic_open = False
                        mic.stop_stream()
                        mic.close()
                        p.terminate()
                        response = {
                            "status": "success",
                            "message": "Mic closed."
                        }
                        await websocket.send(json.dumps(response))
            except json.JSONDecodeError:
                if camera_open:
                    disp_camera(message)
                elif mic_open:
                    play_mic(message)
                else:
                    print("Unknown message:", message)
    except websockets.ConnectionClosed:
        print("Client disconnected.")
        connected_client = None
        if camera_open:
            cv2.destroyAllWindows()
        if mic_open:
            mic.stop_stream()
            mic.close()
            p.terminate()
        pass

async def main():
    async with websockets.serve(handler, host, port):
        await asyncio.get_running_loop().create_future()

if __name__ == '__main__':
    asyncio.run(main())