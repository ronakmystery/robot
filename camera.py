from flask import Flask, Response
from picamera2 import Picamera2
from libcamera import Transform
import cv2

app = Flask(__name__)
picam2 = Picamera2()

picam2.configure(picam2.create_video_configuration(
    main={
        "size": (200, 200),
        "format": "RGB888"
    },
    transform=Transform(rotation=180)
))

# ✅ Set exact FPS using FrameDurationLimits (microseconds)
fps = 10
duration_us = int(1_000_000 / fps)
picam2.video_configuration.controls.FrameDurationLimits = (duration_us, duration_us)

# # Optional image tuning
# picam2.set_controls({
#     "Brightness": 0.3,
#     "Contrast": 0.8,
#     "Saturation": 1.2
# })

picam2.start()

def generate_frames():
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # FIXED: proper format conversion

        _, buffer = cv2.imencode('.jpg', frame)
        jpg_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg_bytes + b'\r\n')

@app.route('/')
def index():
    return '<img src="/stream" style="width: 100%">'

@app.route('/stream')
def stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
