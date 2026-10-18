from fastapi import FastAPI
from fastapi import WebSocket
from fastapi.responses import Response
import json
import base64
from google.cloud import speech
from starlette.websockets import WebSocketDisconnect
from google import genai
from google.cloud import firestore
from fastapi.responses import HTMLResponse


app = FastAPI()
call_transcript = ""
last_gemini_check = 0
analysis_seconds = 0

db = firestore.Client()
speech_client = speech.SpeechClient()
gemini_client = genai.Client(
    vertexai=True,
    project="ai-live-call-guardian-2026",
    location="asia-southeast1"
)

speech_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
    sample_rate_hertz=8000,
    language_code="en-US",
)



@app.get("/")
def home():

    return {
        "service": "Realtime Listener"
    }

@app.get("/alerts")
def get_alerts():

    docs = (
        db.collection("live_call_alerts")
        .order_by(
            "created_at",
            direction=firestore.Query.DESCENDING
        )
        .limit(20)
        .stream()
    )

    alerts = []

    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        alerts.append(item)

    return alerts


@app.websocket("/media")
async def media_stream(
    websocket: WebSocket
):
    global call_transcript
    global last_gemini_check
    global analysis_seconds

    await websocket.accept()

    print("MEDIA_STREAM_CONNECTED", flush=True)

    print("Media Stream Connected")
    audio_buffer = bytearray()

    try:
        while True:
            print("WAITING_FOR_MESSAGE", flush=True)

            data = await websocket.receive_text()

            print("MESSAGE_RECEIVED", flush=True)

            packet = json.loads(data)

            print("EVENT =", packet.get("event"), flush=True)

            event = packet.get("event")

            if event == "media":
        

                payload = packet["media"]["payload"]

                audio_bytes = base64.b64decode(
                    payload
                )
                audio_buffer.extend(audio_bytes)
                print(
                    "BUFFER SIZE:",
                    len(audio_buffer),
                    flush=True
                )
                
                if len(audio_buffer) >= 8000:

                    print(
                        "Buffered:",
                        len(audio_buffer)
                    )

                    audio = speech.RecognitionAudio(
                        content=bytes(audio_buffer)
                    )

                    response = speech_client.recognize(
                        config=speech_config,
                        audio=audio
                    )
                    analysis_seconds += 1
                    print(
                        f"ANALYSIS_SECONDS: {analysis_seconds}",
                        flush=True
                    )

                    for result in response.results:

                        transcript = (
                            result.alternatives[0].transcript
                        )

                

                        call_transcript += (
                            " " + transcript
                        )

                        print(
                            "Transcript:",
                            transcript
                        )

                        print(
                            "FULL:",
                            call_transcript
                        )

                        print(
                            "TRANSCRIPT LENGTH:",
                            len(call_transcript)
                        )

                        print(
                            "CHECK:",
                            len(call_transcript),
                            last_gemini_check,
                            len(call_transcript) - last_gemini_check,
                            flush=True
                        )

                        #if len(call_transcript) - last_gemini_check > 20:
                        if analysis_seconds >= 15:
                            print(
                                "CURRENT LENGTH:",
                                len(call_transcript),
                                
                                flush=True
                            )

                            print(
                                "GEMINI THRESHOLD REACHED",
                                flush=True
                            )
                            print(
                                "CALLING GEMINI",
                                flush=True
                            )

                            prompt = f"""
                                You are an expert scam detection engine for live phone calls.

                                Analyze the transcript and determine whether there are strong indicators of fraud, impersonation, financial scams, social engineering, OTP theft, investment scams, romance scams, or other criminal deception.

                                Be conservative.

                                DO NOT classify a conversation as a scam unless there is clear evidence.

                                Normal family conversations, requests to call relatives, messages between friends, scheduling discussions, customer service interactions, and ordinary business conversations are NOT scams.

                                High-risk indicators include:

                                - Police impersonation
                                - Government impersonation
                                - Bank impersonation
                                - Money laundering accusations
                                - Requests to transfer money
                                - Requests for banking credentials
                                - Requests for OTP codes
                                - Investment guarantees
                                - Cryptocurrency scam solicitations
                                - Romance scam behaviour
                                - Threats of arrest or legal action
                                - Urgent payment demands
                                - Gift card payment requests

                                Return ONLY valid JSON in exactly this format:

                                {{
                                "risk_score": 0,
                                "category": "",
                                "alert": false,
                                "reason": ""
                                }}

                                Rules:

                                - risk_score must be an integer from 0 to 100
                                - alert must be true only when substantial scam indicators exist
                                - category should be "Normal Conversation" if no scam indicators exist
                                - reason should be a short explanation
                                - Do not use markdown
                                - Do not use code fences
                                - Do not include any text before or after the JSON

                                Transcript:

                                {call_transcript}
                                """

                            print("========== ANALYZING ==========")
                            print(call_transcript)
                            print("===============================")



                            try:
                                gemini_response = gemini_client.models.generate_content(
                                    model="gemini-2.5-flash",
                                    contents=prompt
                                )
                                print("========== GEMINI ==========")
                                print(gemini_response.text)
                                print("============================")

                                gemini_text = gemini_response.text.strip()

                                if gemini_text.startswith("```"):
                                    gemini_text = (
                                        gemini_text
                                        .replace("```json", "")
                                        .replace("```", "")
                                        .strip()
                                    )

                                gemini_result = json.loads(
                                    gemini_text
                                )

                                db.collection(
                                    "live_call_alerts"
                                ).add({
                                    "risk_score": gemini_result["risk_score"],
                                    "category": gemini_result["category"],
                                    "alert": gemini_result["alert"],
                                    "reason": gemini_result["reason"],
                                    "transcript": call_transcript,
                                    "created_at": firestore.SERVER_TIMESTAMP
                                })

                                #if gemini_result["risk_score"] >= 70:

                                #    db.collection(
                                #        "live_call_alerts"
                                #    ).add({
                                #        "risk_score": gemini_result["risk_score"],
                                #        "category": gemini_result["category"],
                                #        "alert": gemini_result["alert"],
                                #        "reason": gemini_result["reason"],
                                #        "transcript": call_transcript,
                                #        "created_at": firestore.SERVER_TIMESTAMP
                                #    })

                                #    print(
                                #        "FIRESTORE SAVED",
                                #        flush=True
                                #    )


                            except Exception as e:
                                print(
                                    "GEMINI ERROR:",
                                    str(e),
                                    flush=True
                                )

                            last_gemini_check = len(
                                call_transcript
                            )
                            analysis_seconds = 0

                    
                    audio_buffer.clear()
    


            elif event == "start":

                call_transcript = ""
                last_gemini_check = 0
                analysis_seconds = 0

                print("Stream Started")

            elif event == "stop":

                print(
                    "Stream Stopped"
                )

            #print(data[:200])
    except WebSocketDisconnect:
        print("Client disconnected")

@app.post("/incoming-call")
def incoming_call():

    twiml = """
        <Response>

        <Say voice="alice">
        Welcome to GoEyeVoice.
        Please speak after the tone.
        </Say>

        <Play>https://storage.googleapis.com/goeyevoice-audio/beepsound.mp3</Play>

        <Start>
        <Stream url="wss://realtime-listener-322055493672.asia-southeast1.run.app/media"/>
        </Start>

        <Pause length="600"/>

        </Response>
        """




    return Response(
        content=twiml,
        media_type="text/xml"
    )


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GoEyeVoice Dashboard</title>

        <style>
            body {
                font-family: Arial;
                max-width: 1200px;
                margin: 20px auto;
                padding: 20px;
            }

            .card {
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
            }

            .high {
                border-left: 8px solid red;
            }

            .medium {
                border-left: 8px solid orange;
            }

            .low {
                border-left: 8px solid green;
            }

            h1 {
                color: #d32f2f;
            }
        </style>
    </head>

    <body>

    <h1>GoEyeVoice Live Scam Monitor</h1>

    <button onclick="clearAlerts()"
            style="
                background:red;
                color:white;
                border:none;
                padding:10px 20px;
                border-radius:5px;
                cursor:pointer;
                margin-bottom:20px;
            ">
        Clear Alerts
    </button>

    <div id="alerts"></div>

    <script>

    async function loadAlerts() {

        const response =
            await fetch('/alerts');

        const data =
            await response.json();

        const html =
            data.map(alert => {

                let level = 'low';

                if (alert.risk_score >= 90) {
                    level = 'high';
                }
                else if (alert.risk_score >= 70) {
                    level = 'medium';
                }

                return `
                <div class="card ${level}">

                    <h2>${alert.category}</h2>

                    <p>
                    Risk Score:
                    <b>
                    ${
                        alert.risk_score >= 90
                        ? '🔴'
                        : alert.risk_score >= 70
                        ? '🟠'
                        : '🟢'
                    }
                    ${alert.risk_score}
                    </b>
                    </p>

                    <p>
                    <b>Time:</b>
                    ${alert.created_at}
                    </p>

                    <p>
                    ${alert.reason || 'No reason available'}
                    </p>

                    <hr>

                    <p>
                    ${alert.transcript}
                    </p>

                </div>
                `;
            }).join('');

        document.getElementById(
            'alerts'
        ).innerHTML =
            html ||
            '<h2>No alerts found</h2>';
    }

    async function clearAlerts() {

        await fetch(
            '/clear-alerts',
            {
                method: 'POST'
            }
        );

        loadAlerts();
    }

    loadAlerts();

    setInterval(
        loadAlerts,
        5000
    );

    </script>

</body>
    </html>
    """

@app.post("/clear-alerts")
def clear_alerts():

    docs = db.collection(
        "live_call_alerts"
    ).stream()

    for doc in docs:
        doc.reference.delete()

    return {
        "status": "success"
    }