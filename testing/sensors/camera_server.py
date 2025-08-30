#!/usr/bin/env python3
from flask import Flask, Response
from picamera2 import Picamera2, encoders, outputs
import io, threading

app = Flask(__name__)
picam2 = Picamera2()

# Simple video config
picam2.configure(picam2.create_video_configuration(main={"size": (500, 500)}))

# Limit FPS
fps = 10
dur = int(1_000_000 / fps)
picam2.video_configuration.controls.FrameDurationLimits = (dur, dur)

# Output that always keeps the latest frame
class Output(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.cond = threading.Condition()
    def writable(self): return True
    def write(self, buf):
        if buf.startswith(b"\xff\xd8"):  # new JPEG
            with self.cond:
                self.frame = buf
                self.cond.notify_all()
        return len(buf)

output = Output()
picam2.start_recording(encoders.MJPEGEncoder(), outputs.FileOutput(output))

def gen():
    while True:
        with output.cond:
            output.cond.wait()
            frame = output.frame
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"

@app.route("/")
def index():
    return '<img src="/stream" style="width:100%; transform:rotate(90deg);">'

@app.route("/stream")
def stream():
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    app.run("0.0.0.0", 8000, threaded=True)
