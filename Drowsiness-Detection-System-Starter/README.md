# Drowsiness Detection System — starter

A Flask web prototype with responsive desktop/mobile layouts. The visitor's camera is accessed by their browser, and a basic Eye Aspect Ratio (EAR) heuristic runs with MediaPipe Face Mesh. Camera frames are not uploaded to Flask.

## Important limitations
- Educational prototype only, not a certified driver-safety system or medical device. Never rely on it to decide whether driving is safe.
- EAR threshold and duration are heuristic defaults and are not validated for real-world drowsiness detection. Lighting, camera angle, glasses, facial variation, and ordinary blinks can cause errors.
- Camera and location permissions require HTTPS on a deployed site (localhost works for development).
- SMS/WhatsApp remain disabled until a messaging provider is configured. Provider availability, sender authorization, WhatsApp setup, recipient opt-in, and costs may apply.
- Contact details are stored in the browser's local storage on that device; they are not stored by this Flask app.
- MediaPipe is loaded from a CDN, so an internet connection is required.

## Run locally on Windows
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```
Open `http://127.0.0.1:5000`.

If activation is blocked:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Messaging configuration
Configure provider credentials only in a local `.env` file or the hosting provider's secret settings. Never commit real credentials or place them in browser JavaScript. Use only with informed consent and recipients who agreed to receive alerts. The alert deliberately says “possible prolonged eye-closure event” because false positives can occur.

## Deploy
Deploy as a Python Flask app using `gunicorn app:app`, set environment variables in the host dashboard, and use HTTPS. Test camera and location permissions on desktop and mobile before sharing the URL.
