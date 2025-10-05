#!/usr/bin/python3
from flask import Flask, Response
from picamera2 import Picamera2, encoders
from picamera2.outputs import FileOutput
import io, threading

app = Flask(__name__)
picam2 = Picamera2()

# Configure smaller frame size for Pi Zero + phone streaming
video_config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(video_config)

# Output buffer that always keeps the latest frame
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()
    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):  # JPEG SOI marker
            with self.condition:
                self.frame = buf
                self.condition.notify_all()

output = StreamingOutput()
picam2.start_recording(encoders.MJPEGEncoder(), FileOutput(output))

def gen():
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return '<img src="/stream" style="width:100%; transform: rotate(180deg);">'

@app.route('/stream')
def stream():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, threaded=True)