from clarifai import rest
from clarifai.rest import ClarifaiApp
from clarifai.rest import Image as ClImage
import json
import cv2
from camera import VideoCamera

def pprint(x):
    print(json.dumps(x, indent = 2, sort_keys = True))

cam = VideoCamera()
img = None
while True:
    jpeg, img = cam.get_frame()
    cv2.imshow("my webcam", img)
    ch = cv2.waitKey(1)
    '''if ch == 27:
        break
    if ch == 32:
        print("taken")
        cv2.imwrite("thepic.jpg", img)
        break'''

del(cam)
cv2.destroyAllWindows()

app = ClarifaiApp(api_key = "d556e0ea9bd741d98e6fe8f4812f1b44")

model = app.models.get('bd367be194cf45149e75f01d59f77ba7')
# image = ClImage(file_obj=open('pizza.jpg', 'rb'))
img_str = cv2.imencode('.jpg', img)[1].tostring()
image = app.inputs.create_image_from_bytes(img_bytes = img_str)
resp = model.predict([image])

pprint(resp)
