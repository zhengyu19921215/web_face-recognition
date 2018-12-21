# *_*coding:utf-8 *_*

from flask_uploads import *
from flask import *
import logging
import numpy as np
import cv2
import face_recognition
import PIL.Image as Image
import json
import base64
from flask_script import Manager

########################################logger##############################
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Start print log")
logger.debug("Do something")
logger.warning("Something maybe fail.")
logger.info("Finish")
########################################logger##############################

########################################app config##########################
UPLOADS_DEFAULT_DEST="C:/Users/zhengyu1/Desktop/flask_web3/flask_web3/static/images/"
app = Flask(__name__)
app.config['UPLOADS_DEFAULT_DEST'] = UPLOADS_DEFAULT_DEST
app.config['UPLOADED_PHOTO_ALLOW'] = IMAGES
app.config['UPLOADS_DEFAULT_URL'] = 'http://0.0.0.0:5000/'

manager=Manager(app)

uploaded_photos = UploadSet()
configure_uploads(app, uploaded_photos)
########################################app config##########################

ALLOWED_EXTENSIONS = ['png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF']
global known_faces
global known_names


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/',methods=['GET', 'POST'])
def index():
    return render_template('index.html')

def set_target_encoding(file):
    img = face_recognition.load_image_file(file)
    return face_recognition.face_encodings(img)[0]

@app.route('/uploadImage', methods=['GET','POST'])
def uploadImage():
    global known_faces
    global known_names
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            logger.debug('No file part')
            return jsonify({'code': -1, 'filename': '', 'msg': 'No file part'})
        file = request.files['file']
        # if user does not select file, browser also submit a empty part without filename
        if file.filename == '':
            logger.debug('No selected file')
            return jsonify({'code': -1, 'filename': '', 'msg': 'No selected file'})
        else:
            try:
                filename = uploaded_photos.save(file)
                known_faces=set_target_encoding(file)
                known_names=filename[:filename.index('.')]

                logger.debug('%s url is %s' % (filename, uploaded_photos.url(filename)))
                return jsonify({'code': 0, 'filename': filename, 'msg': uploaded_photos.url(filename)})
            except Exception as e:
                logger.debug('upload file exception: %s' % e)
                return jsonify({'code': -1, 'filename': '', 'msg': 'Error occurred'})
    else:
        return jsonify({'code': -1, 'filename': '', 'msg': 'Method not allowed'})

def restore_img(byte_string):
    data=json.loads(byte_string)

    width = data['width']
    height = data['height']
    img_list = [float(i) for i in data['img'].split(',')]

    r_list = [img_list[i - 1] for i in range(1, len(img_list) + 1) if i % 4 == 1]
    g_list = [img_list[i - 1] for i in range(1, len(img_list) + 1) if i % 4 == 2]
    b_list = [img_list[i - 1] for i in range(1, len(img_list) + 1) if i % 4 == 3]

    r_array=np.array(r_list)
    r_array=r_array.reshape((height,width))
    g_array = np.array(g_list)
    g_array = g_array.reshape((height, width))
    b_array = np.array(b_list)
    b_array = b_array.reshape((height, width))

    r = Image.fromarray(r_array).convert('L')
    g = Image.fromarray(g_array).convert('L')
    b = Image.fromarray(b_array).convert('L')

    img = Image.merge("RGB", (r, g, b))
    return img

def get_frame(image):
    global known_faces
    global known_names
    global count
    rgb_frame=image

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    face_names = []
    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        match = face_recognition.compare_faces([known_faces], face_encoding, tolerance=0.50)

        name = None
        if match[0]:
            name = known_names
        face_names.append(name)

    # Label the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        if not name:
            continue

        # Draw a box around the face
        cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(image, (left, bottom - 25), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(image, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

    # Write the resulting image to the output video file

    ret, jpeg = cv2.imencode('.jpg', image)

    # 对于 python2.7 或者低版本的 numpy 请使用 jpeg.tostring()
    return jpeg.tobytes()

@app.route('/getVideo', methods=['POST'])
def getVideo():
    global count
    image = restore_img(request.data)
    image=image.convert('RGB')
    bytes=get_frame(np.array(image))
    x = base64.b64encode(bytes)
    return Response(x)

@manager.option("-h",'--host',dest="host",default="0.0.0.0")
@manager.option("-p",'--port',dest="port",default=5000)
def run(host,port):
    app.run(host=host,port=port,ssl_context=("C:/users/zhengyu1/desktop/flask_web3/server.crt","C:/users/zhengyu1/desktop/flask_web3/server.key"))

if __name__ == '__main__':
    manager.run()