async_mode = None

import time
from flask import Flask, render_template
import socketio
from camera import VideoCamera
from clarifai import rest
from clarifai.rest import ClarifaiApp
from clarifai.rest import Image as ClImage
import json, base64, cv2

sio = socketio.Server(logger=True, async_mode=async_mode)
app = Flask(__name__)
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
app.config['SECRET_KEY'] = 'secret!'
thread = None
ai = ClarifaiApp(api_key = "d556e0ea9bd741d98e6fe8f4812f1b44")
model = ai.models.get('bd367be194cf45149e75f01d59f77ba7')

def pprint(x):
    print(json.dumps(x, indent = 2, sort_keys = True))


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    cam = VideoCamera()
    while True:
        sio.sleep(5)
        img = cam.get_frame()
        raw_img = cam.get_frame_raw()
        cv2.imshow("the image", raw_img)
        ai_image = ai.inputs.create_image_from_bytes(img_bytes = img)
        resp = model.predict([ai_image])
        pprint(resp)
        count += 1
        sio.emit('food_type', {'food' : json.dumps(resp["outputs"][0]["data"]["concepts"], indent = 2, sort_keys = True), 'image': base64.b64encode(img)}, broadcast = True)


@app.route('/')
def index():
    global thread
    if thread is None:
        thread = sio.start_background_task(background_thread)
    return render_template('index.html')


@sio.on('connect')
def test_connect(sid, environ):
    sio.emit('my response', {'data': 'Connected', 'count': 0}, broadcast = True)


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
