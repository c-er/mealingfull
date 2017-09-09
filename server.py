async_mode = None

import time
from flask import Flask, render_template, send_from_directory
import socketio
from camera import VideoCamera
from clarifai import rest
from clarifai.rest import ClarifaiApp
from clarifai.rest import Image as ClImage
from twilio.rest import Client
import json, base64, cv2

sio = socketio.Server(logger=True, async_mode=async_mode)
app = Flask(__name__)
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
app.config['SECRET_KEY'] = 'secret!'
thread = None
ai = ClarifaiApp(api_key = "d556e0ea9bd741d98e6fe8f4812f1b44")
model = ai.models.get('bd367be194cf45149e75f01d59f77ba7')

legal_foods = ["french fries", "bread", "water", "ketchup", "apple"]

last_foods = []
numbers = ["6094774055"]

twilio_origin = "+12674940179"
twilio_sid = "AC7c140f99da2450bf3895ef2f80684e71"
twilio_token = "77184e815128509653ea695fe85342df"
twilio_client = Client(twilio_sid, twilio_token)

def pprint(x):
    print(json.dumps(x, indent = 2, sort_keys = True))

def process_list(l):
    return list(map(lambda x: x["name"], list(filter(lambda x: x["name"] in legal_foods and x["value"] > 0.7, l))))


def background_thread():
    """Example of how to send server generated events to clients."""
    global last_foods, numbers
    count = 0

    while True:
        cam = cv2.VideoCapture(0)
        print("grabbing frame")
        ret, raw = cam.read()
        ret, jpg = cv2.imencode(".jpg", raw)
        img = jpg.tobytes()
        cv2.waitKey(1)
        ai_image = ai.inputs.create_image_from_bytes(img_bytes = img)
        resp = model.predict([ai_image])
        pprint(resp)
        count += 1
        list_of_concepts = resp["outputs"][0]["data"]["concepts"]
        current_foods = process_list(list_of_concepts)

        if(current_foods != last_foods):
            last_foods = current_foods
            for n in numbers:
                twilio_client.messages.create(from_=twilio_origin, to=n, body="Food Changed: It's now " + str(current_foods))

        sio.emit('food_type', {'food' : current_foods, 'image': resp["outputs"][0]["input"]["data"]["image"]["url"]}, broadcast = True)
        print(resp["outputs"][0]["input"]["data"]["image"]["url"])
        cam.release()
        sio.sleep(5)

@app.route('/')
def index():
    global thread
    if thread is None:
        thread = sio.start_background_task(background_thread)
    return render_template('index.html')

@app.route("/assets/<path:path>")
def send_asset(path):
    return send_from_directory("assets", path)

if __name__ == '__main__':
    if sio.async_mode == 'threading':
        # deploy with Werkzeug
        app.run(threaded=True)
    elif sio.async_mode == 'eventlet':
        # deploy with eventlet
        import eventlet
        import eventlet.wsgi
        eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
    elif sio.async_mode == 'gevent':
        # deploy with gevent
        from gevent import pywsgi
        try:
            from geventwebsocket.handler import WebSocketHandler
            websocket = True
        except ImportError:
            websocket = False
        if websocket:
            pywsgi.WSGIServer(('', 5000), app,
                              handler_class=WebSocketHandler).serve_forever()
        else:
            pywsgi.WSGIServer(('', 5000), app).serve_forever()
    elif sio.async_mode == 'gevent_uwsgi':
        print('Start the application through the uwsgi server. Example:')
        print('uwsgi --http :5000 --gevent 1000 --http-websockets --master '
              '--wsgi-file app.py --callable app')
    else:
        print('Unknown async_mode: ' + sio.async_mode)
