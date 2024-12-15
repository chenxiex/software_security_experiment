import asyncio
import websockets
import json
import cv2  # 导入 OpenCV
import pyaudio  # 导入 PyAudio

# Envs
port = 8765
host="localhost"

connected_client = None
connected_frontend = None
camera_open = False
cap = None
mic_open = False
audio_stream = None

async def send_camera_feed():
    global connected_client
    global camera_open
    global cap
    websocket=connected_client
    while camera_open and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = buffer.tobytes()
        await websocket.send(jpg_as_text)
        await asyncio.sleep(0.04)  # 控制帧率

async def send_audio_feed():
    global connected_client
    global mic_open
    global audio_stream
    websocket = connected_client
    while mic_open:
        data = audio_stream.read(1024)
        await websocket.send(data)
        await asyncio.sleep(0.01)  # 控制音频传输速率

async def handler(websocket):
    global connected_client
    global connected_frontend
    global camera_open
    global cap
    global mic_open
    global audio_stream
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
            data = json.loads(message)
            if data['action'] == 'ping':
                response = {
                    "status": "success",
                }
                await websocket.send(json.dumps(response))
            elif data['action'] == 'camera':
                if data['mode'] == 'open':
                    print("Opening camera...")
                    if not camera_open:
                        cap = cv2.VideoCapture(0)
                        camera_open = True
                    if cap.isOpened():
                        response = {
                            "status": "success",
                            "message": "Camera opened."
                        }
                        await websocket.send(json.dumps(response))
                    else:
                        response = {
                            "status": "error",
                            "message": "Failed to open camera."
                        }
                        await websocket.send(json.dumps(response))
                        continue
                    print("Preparing to send camera feed...")
                    asyncio.create_task(send_camera_feed())
                elif data['mode'] == 'close':
                    print("Closing camera...")
                    if camera_open:
                        camera_open = False
                        cap.release()
                    print("Camera closed.")
                    response = {
                        "status": "success",
                        "message": "Camera closed."
                    }
                    await websocket.send(json.dumps(response))
            elif data['action'] == 'mic':
                if data['mode'] == 'open':
                    print("Opening microphone...")
                    if not mic_open:
                        p = pyaudio.PyAudio()
                        audio_stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
                        mic_open = True
                    if mic_open:
                        response = {
                            "status": "success",
                            "message": "Microphone opened."
                        }
                        await websocket.send(json.dumps(response))
                        print("Preparing to send audio feed...")
                        asyncio.create_task(send_audio_feed())
                    else:
                        response = {
                            "status": "error",
                            "message": "Failed to open microphone."
                        }
                        await websocket.send(json.dumps(response))
                elif data['mode'] == 'close':
                    print("Closing microphone...")
                    if mic_open:
                        mic_open = False
                        audio_stream.stop_stream()
                        audio_stream.close()
                        p.terminate()
                    print("Microphone closed.")
                    response = {
                        "status": "success",
                        "message": "Microphone closed."
                    }
                    await websocket.send(json.dumps(response))
                else:
                    response = {
                        "status": "error",
                        "message": "Invalid request."
                    }
                    await websocket.send(json.dumps(response))
    except websockets.ConnectionClosed:
        print("Client disconnected.")
        connected_client = None
        if camera_open:
            camera_open = False
            cap.release()
        if mic_open:
            mic_open = False
            audio_stream.stop_stream()
            audio_stream.close()
            p.terminate()
        pass

async def main():
    async with websockets.serve(handler, host, port):
        await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())