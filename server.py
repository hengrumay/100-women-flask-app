from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename
import os
import subprocess
# import speech_recognition as sr
from pydub import AudioSegment

from model import db, connect_to_db, User

import nlp

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/emplify'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = '/tmp/'
ALLOWED_EXTENSIONS = set(['wav','m4a', 'caf'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'


# Set "homepage" to index.html
@app.route('/')
def index():
    # print (nlp.to_spacy_doc())
    # print (nlp.to_textacy_doc())
    return render_template('index.html')

# Save e-mail to database and send to success page
@app.route('/prereg', methods=['POST'])
def prereg():
    email = None
    if request.method == 'POST':
        email = request.form['email']
        # Check that email does not already exist (not a great query, but works)
        if not db.session.query(User).filter(User.email == email).count():
            reg = User(email)
            db.session.add(reg)
            db.session.commit()
            return render_template('success.html')
    return render_template('index.html')



def allowed_file(filename):
    print 'in allowed file'
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            # print 'file not in request.files'
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
      
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            # print 'no selected file'
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # print 'file is allowed'
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_path_pre_extension, extension = file_path.split('.')
            file.save(file_path)

            if extension == 'caf':
                converted_file = file_path_pre_extension + '.wav'
                command = 'afconvert -f WAVE -d UI8 {file_path} {converted_file}'.format(file_path=file_path, converted_file=converted_file)
                subprocess.call(command, shell=True)


        # r = sr.Recognizer()
        # if filename.rsplit('.', 1)[1].lower() == 'm4a':
        #     m4_audio = AudioSegment.from_file(app.config['UPLOAD_FOLDER']+filename, format="m4a")
        #     m4_audio.export("sound_file.wav", format="wav")
        #     filename = "sound_file.wav"
        #     file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # with sr.WavFile(filename) as source:
                    # audio = r.record(source)
        # else:
        #     with sr.WavFile(app.config['UPLOAD_FOLDER']+filename) as source:
        #             audio = r.record(source)

        # try:
        #     flash("Transcription: " + r.recognize_google(audio))
        # except LookupError:
        #     flash("Could not understand audio")
    return render_template('index.html')


if __name__ == '__main__':
    connect_to_db(app)
    app.debug = True
    app.run()
