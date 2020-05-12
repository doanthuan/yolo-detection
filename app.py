from __future__ import division
import os
from flask import Flask, request, redirect, url_for, render_template, flash, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename
from datetime import datetime
from utils import *

app = Flask(__name__)


app.config['UPLOAD_FOLDER'] = 'uploads'

# @app.route('/')
# def dirtree():
#     path = os.path.expanduser(u'~')
#     return render_template('dirtree.html', tree=make_tree(path))

@app.route('/', methods=['GET'])
def index(name=None):
    return render_template("upload.html")

@app.route('/upload', methods=['GET','POST'])
def upload(name=None):
    if request.method == 'POST':
        # upload audio and transcribe the file
        # check if the post request has the file part
        if 'upload_file' not in request.files:
            return 'No file part'
        file = request.files['upload_file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return 'No selected file'

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        return redirect(url_for('video_feed', name=filename))
    else:
        return render_template('upload.html')

def parse_video(filename):

    net, output_layers, classes, colors = init_net()

    # Read from video file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    cap = cv2.VideoCapture(filepath)
    # out = cv2.VideoWriter(path,fourcc, 20, (460,360))

    # define a box of Roid
    frame_number = 0
    objectID = 0
    frame_number = 0
    frame = None
    prev_frame = None
    while (cap.isOpened()):
        #start_time = time.time()
        ret_val, frame = cap.read()
        if frame is None:
            break
        if prev_frame is not None:
            # --- take the absolute difference of the images ---
            res = cv2.absdiff(frame, prev_frame)
            # --- convert the result to integer type ---
            res = res.astype(np.uint8)
            # --- find percentage difference based on number of pixels that are not zero ---
            percentage = (np.count_nonzero(res) * 100) / res.size

            if (percentage>10):
                frame = detect_gun(net, output_layers, frame, classes, colors)
        else:
            frame = detect_gun(net, output_layers, frame, classes, colors)

        prev_frame = frame
        frame_number = frame_number + 1

        cv2.putText(frame, str(frame_number), (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        # yield the output frame in the byte format
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')

    cap.release()


@app.route("/video_feed")
def video_feed():
	# return the response generated along with the specific media
	# type (mime type)
    filename = request.args['name']  
    # counterpart for url_for()
    return Response(parse_video(filename), mimetype = "multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True, host='0.0.0.0', port=5000)