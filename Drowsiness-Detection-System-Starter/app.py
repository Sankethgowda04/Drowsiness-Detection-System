import os
import re

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(**name**)

def valid_phone(value: str) -> bool:
"""Validate a 10-digit Indian mobile number."""
return bool(re.fullmatch(r"[6-9][0-9]{9}", value or ""))

@app.get("/")
def index():
return render_template("index.html")

@app.get("/health")
def health():
return jsonify({
"status": "ok",
"app": "Drowsiness Detection System"
})

@app.post("/api/alert")
def send_alert():
"""Send a consented alert using a validated Indian mobile number."""


data = request.get_json(silent=True) or {}

# 1. Require consent before sending an alert.
if data.get("consent") is not True:
    return jsonify({
        "ok": False,
        "message": "Alert sharing consent is required."
    }), 400

# 2. Validate the 10-digit Indian mobile number.
contact = str(data.get("contact") or "").strip()

if not valid_phone(contact):
    return jsonify({
        "ok": False,
        "message": "Enter a valid 10-digit Indian mobile number."
    }), 400

# 3. Add India's country code automatically.
contact = "+91" + contact

# 4. Read messaging configuration.
sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
sms_from = os.getenv("TWILIO_SMS_FROM", "").strip()
whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM", "").strip()

# 5. Check whether a messaging provider is configured.
if not (sid and token and (sms_from or whatsapp_from)):
    return jsonify({
        "ok": False,
        "configured": False,
        "message": (
            "Demo mode: no message was sent. The site owner "
            "must configure a messaging provider."
        )
    }), 503

# 6. Accept only Google Maps URLs for the location field.
maps_url = str(data.get("maps_url") or "").strip()

if not maps_url.startswith("https://www.google.com/maps"):
    maps_url = ""

# 7. Prepare the alert message.
body = (
    "DrowsinessGuard: A possible prolonged eye-closure event "
    "was detected. Automated alerts may be incorrect. "
    "Please check that the person is safe.\n"
    + (
        f"Location: {maps_url}"
        if maps_url
        else "Location was not shared."
    )
)

# 8. Send SMS and/or WhatsApp alerts.
try:
    from twilio.rest import Client

    client = Client(sid, token)
    sent = []
    errors = []

    # Send SMS if configured.
    if sms_from:
        try:
            client.messages.create(
                body=body,
                from_=sms_from,
                to=contact
            )
            sent.append("SMS")
        except Exception:
            app.logger.exception("SMS sending failed.")
            errors.append("SMS sending failed.")

    # Send WhatsApp if configured.
    if whatsapp_from:
        wa_from = (
            whatsapp_from
            if whatsapp_from.startswith("whatsapp:")
            else "whatsapp:" + whatsapp_from
        )

        wa_to = "whatsapp:" + contact

        try:
            client.messages.create(
                body=body,
                from_=wa_from,
                to=wa_to
            )
            sent.append("WhatsApp")
        except Exception:
            app.logger.exception("WhatsApp sending failed.")
            errors.append("WhatsApp sending failed.")

    # Report whether at least one message was submitted.
    if sent:
        return jsonify({
            "ok": True,
            "message": "Alert submitted via " + " and ".join(sent) + ".",
            "channels": sent,
            "errors": errors
        }), 200

    return jsonify({
        "ok": False,
        "message": "Messaging failed. Check provider configuration and permissions.",
        "errors": errors
    }), 502

except Exception:
    app.logger.exception("Messaging provider initialization failed.")
    return jsonify({
        "ok": False,
        "message": (
            "Messaging failed. Check provider configuration "
            "and permissions."
        )
    }), 502

if **name** == "**main**":
app.run(
host="127.0.0.1",
port=int(os.getenv("PORT", "5000")),
debug=False
)
