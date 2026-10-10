import cv2
import time
import threading
import pygame
from flask import Flask, render_template, Response, jsonify

app = Flask(__name__)

eye_closed_start = None
alarm_on = False
closed_counter = 0
THRESHOLD = 10

pygame.mixer.init()
ALARM_SOUND = "static/alarm.mp3"
alarm_channel = None


class VideoCamera:
    def __init__(self):
        self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not self.video.isOpened():
            raise Exception("Cannot open webcam")

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

    def __del__(self):
        if self.video.isOpened():
            self.video.release()

    def play_alarm(self):
        global alarm_channel

        if not pygame.mixer.get_busy():
            sound = pygame.mixer.Sound(ALARM_SOUND)
            alarm_channel = sound.play(-1)

    def stop_alarm(self):
        global alarm_channel

        if alarm_channel:
            alarm_channel.stop()
            alarm_channel = None

    def get_frame(self):
        global eye_closed_start, alarm_on, closed_counter

        success, frame = self.video.read()

        if not success or frame is None:
            return None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        eyes_detected = False

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            roi_gray = gray[y:y+h, x:x+w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray)

            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(
                    frame[y:y+h, x:x+w],
                    (ex, ey),
                    (ex+ew, ey+eh),
                    (0, 255, 0),
                    2
                )

            if len(eyes) >= 2:
                eyes_detected = True

        if not eyes_detected:
            if eye_closed_start is None:
                eye_closed_start = time.time()

            closed_counter = int(time.time() - eye_closed_start)

            if closed_counter >= THRESHOLD and not alarm_on:
                alarm_on = True
                threading.Thread(
                    target=self.play_alarm,
                    daemon=True
                ).start()

        else:
            eye_closed_start = None
            closed_counter = 0

            if alarm_on:
                alarm_on = False
                self.stop_alarm()

        cv2.putText(
            frame,
            f"Status: {'ALARM!' if alarm_on else 'Monitoring'}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255) if alarm_on else (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Closed: {closed_counter}s",
            (10, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        _, jpeg = cv2.imencode(".jpg", frame)

        return jpeg.tobytes()


camera = VideoCamera()


def gen(cam):
    while True:
        frame = cam.get_frame()

        if frame is not None:
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                frame +
                b'\r\n\r\n'
            )


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/video_feed')
def video_feed():
    return Response(
        gen(camera),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/status')
def status():
    return jsonify({
        "eyes_closed": closed_counter > 0,
        "eyes_closed_counter": closed_counter,
        "alarm_on": alarm_on,
        "threshold": THRESHOLD
    })


@app.route('/reset_alarm')
def reset_alarm():
    global closed_counter, alarm_on, eye_closed_start

    closed_counter = 0
    alarm_on = False
    eye_closed_start = None

    camera.stop_alarm()

    return jsonify({"status": "reset"})


if __name__ == "__main__":
    print("🚀 Drowsiness Detection Started")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True,
        use_reloader=False
    )