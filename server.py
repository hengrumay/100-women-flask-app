# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import subprocess
# import speech_recognition as sr
from pydub import AudioSegment
from collections import defaultdict

from model import db, connect_to_db, User
from helpers import transcribe

import nlp
import json

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/emplify'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = '/tmp/'
ALLOWED_EXTENSIONS = set(['wav','m4a', 'caf'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

# @app.route('/upload', methods=['GET', 'POST'])
# def process_speech():
#     wav_file = file_to_use
#     watson_json= transcribe_watson(wav_file)
#     df = makeDFfromJson(watson_json)
#     speaker_dict = retrieveSpeakerInfoAsDict(df)
#     for speaker in speaker_dict:
#         speaker["name"] = get_name_from_first_sentence(sentences) or speaker
#         # if speaker["name"]==None:
#         #        speaker["name"] = speaker #default to speaker's ID number
#         speaker["top_cats"] = get_semantic_categories(sentences)
#     #save speaker_dict to file
#     with open('speaker_dict.json', 'w') as fp:
#         json.dumps(speaker_dict, fp)
#
#     return jsonify(speaker_dict=speaker_dict)



@app.route('/names', methods=['GET'])
def get_names():
    names = defaultdict(str)
    with open('speaker_dict.json', 'r') as fp:
        speaker_dict = json.loads(fp)
    for speaker in speaker_dict:
        names[speaker] = speaker["name"] # e.g. {0:"Erin"}
        # OR names[speaker["name"]] = speaker    # e.g. {Erin:"0"}
    return jsonify(names=names)

@app.route('/results', methods=['GET'])
def get_results():
    with open('speaker_dict.json', 'r') as fp:
        results = json.loads(fp)
    return results

# Set "homepage" to index.html
@app.route('/')
def index():
    # print (nlp.to_spacy_doc())
    # print (nlp.to_textacy_doc())
    return render_template('index.html')


def allowed_file(filename):
    print('in allowed file')
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

            file_to_use = file_path

            if extension == 'm4a':
                m4_audio = AudioSegment.from_file(file_path)
                m4_audio.export(file_path_pre_extension+".wav", format="wav")
                file_to_use = file_path_pre_extension+".wav"


            if extension == 'caf' or extension=='m4a':
                converted_file = file_path_pre_extension + '.wav'
                command = 'afconvert -f WAVE -d UI8 {file_path} {converted_file}'.format(file_path=file_path, converted_file=converted_file)
                subprocess.call(command, shell=True)
                file_to_use = converted_file

            wav_file = file_to_use
            watson_json= transcribe_watson(wav_file)
            df = makeDFfromJson(watson_json)
            speaker_dict = retrieveSpeakerInfoAsDict(df)
            for speaker in speaker_dict:
                speaker["name"] = get_name_from_first_sentence(sentences) or speaker
                # if speaker["name"]==None:
                #        speaker["name"] = speaker #default to speaker's ID number
                speaker["top_cats"] = get_semantic_categories(sentences)
            #save speaker_dict to file
            with open('speaker_dict.json', 'w') as fp:
                json.dumps(speaker_dict, fp)

        # r = sr.Recognizer()
        # if filename.rsplit('.', 1)[1].lower() == 'm4a':
        #     m4_audio = AudioSegment.from_file(app.config['UPLOAD_FOLDER']+filename, format="m4a")
        #     m4_audio.export("sound_file.wav", format="wav")
            #filename = "sound_file.wav"
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
