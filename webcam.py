
'''
Simply display the contents of the webcam with optional mirroring using OpenCV
via the new Pythonic cv2 interface.  Press <esc> to quit.
'''

import cv2

def main():
    img_number = 0
    cam = cv2.VideoCapture(0)
    while True:
        ret, img = cam.read()
        cv2.imshow("my webcam", img)
        ch = cv2.waitKey(1)
        if ch == 27:
            break
        if ch == 32:
            print("saving")
            cv2.imwrite("test_%d.png" % img_number, img)
            img_number += 1

    cam.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
	main()
