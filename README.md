一个简单的服务器，打开并传输服务器上的摄像头和麦克风。默认情况下仅监听本地的8765端口。
```
pip install -r requirements.txt
python server.py
```
- server.py 服务器端
- client.py 用于解析服务器端传输的数据。需要搭配额外的连接控制程序使用。(尚未测试)
- test.py 一个简单的测试程序，演示了server.py的麦克风功能。