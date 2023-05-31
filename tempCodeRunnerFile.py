from flask import Flask, render_template, request, jsonify
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing import image
from tensorflow.keras.optimizers import RMSprop
import tensorflow as tf
import numpy as np
import tesseract as ts
import re
import imquality.brisque as brisque
import PIL.Image
import matplotlib.pyplot as plt
from pymongo import MongoClient
from PIL import Image
import random


def save_data(indata):
    client = MongoClient('mongodb://localhost:27017'
                         )  # Replace with your MongoDB connection string
    db = client['CollegeProj']  # Replace with your database name
    collection = db['SubmitData']  # Replace with your collection name
    data = indata  # Assuming data is sent as JSON in the request body
    collection.insert_one(data)
    return 'Data saved successfully!'


def get_data():
    client = MongoClient('mongodb://localhost:27017'
                         )  # Replace with your MongoDB connection string
    db = client['CollegeProj']  # Replace with your database name
    collection = db['SubmitData']  # Replace with your collection name
    data = collection.find()
    return data


#Verhoff Algorithm
mult = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6], [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]]
perm = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
        [5, 8, 0, 3, 7, 9, 6, 1, 4, 2], [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
        [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
        [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]]


def find_matching_strings(arr, regex_pattern):
    matching_strings = None
    print(arr)
    p = re.compile(regex_pattern)
    for string in arr:
        if re.search(p, string.upper()):
            matching_strings = string.upper()
    return matching_strings


def Validate(aadharNum):
    try:
        i = len(aadharNum)
        j = 0
        x = 0

        while i > 0:
            i -= 1
            x = mult[x][perm[(j % 8)][int(aadharNum[i])]]
            j += 1
        if x == 0:
            return 'Valid Aadhar Number'
        else:
            return 'Invalid Aadhar Number'

    except ValueError:
        return 'Invalid Aadhar Number'
    except IndexError:
        return 'Invalid Aadhar Number'


model = tf.keras.models.load_model('FinalModel.h5')
app = Flask(__name__)


@app.route('/')
def home():
    return render_template('upload.html')


@app.route('/admin')
def get_list():
    data = get_data()
    return render_template('admin.html', data=data)


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    f = None
    fname = ""
    lname = ""
    if request.method == 'POST':
        f = request.files['file']
        f.save("test.jpg")

        fname = request.form.get("fname").lower()
        lname = request.form.get("lname").lower()

    img = image.load_img('test.jpg', target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x /= 255.
    prediction = model.predict(x)
    val = np.argmax(prediction)
    select = request.form.get("Type")

    if val == 1 and int(select) != 1:
        return (render_template('fail.html'))
    if val == 0 and int(select) != 0:
        return (render_template('fail.html'))
    nameloc = 0
    if val == 1:
        result = ts.readStream('test.jpg')
        for i in range(len(result)):
            if result[i] == fname:
                nameloc = i
        pannumber = find_matching_strings(result, "[A-Z]{5}[0-9]{4}[A-Z]{1}")
        if pannumber == None:
            return jsonify(
                inputName=fname + lname,
                nameonCard=result[nameloc] + result[nameloc + 1],
                isvalid=False,
                doctype="PAN",
                validstatus=
                f"The Card is not accepted,Please Check whether it is real")
        if ((fname in result) and (lname in result)):
            x = random.randint(0, 1000)
            img = Image.open('test.jpg')
            img.save(f"static/Submitteddata/{x}.jpg")
            data = {
                'name': fname + " " + lname,
                'path': f"{x}.jpg",
                'isValid': True,
                'DocType': "PAN",
                'IdNo': pannumber
            }
            save_data(data)
            return jsonify(
                inputName=fname + lname,
                nameonCard=result[nameloc] + result[nameloc + 1],
                isvalid=True,
                doctype="PAN",
                pan_no=pannumber,
                validstatus=f"The Card is Valid and It belongs to {fname+lname}"
            )
        else:
            return jsonify(
                inputName=fname + lname,
                nameonCard="Invalid",
                isvalid=False,
                doctype="PAN",
                pan_no=pannumber,
                validstatus=
                f"The Card is a Pan Card,The Card does not belong to you, Please Upload valid Card"
            )
    elif val == 0:
        inputAadharNumber = request.form.get("AadharNumber").lower()
        result = ts.readStream('test.jpg')
        for i in range(len(result)):
            if result[i] == fname:
                nameloc = i
        if ((fname in result) and (lname in result)):
            x = random.randint(0, 1000)
            img = Image.open('test.jpg')
            img.save(f"static/Submitteddata/{x}.jpg")
            data = {
                'name': fname + " " + lname,
                'path': f"{x}.jpg",
                'isValid': True,
                'DocType': "AADHAR",
                'IdNo': inputAadharNumber
            }
            save_data(data)

            return jsonify(
                inputName=fname + lname,
                nameonCard=result[nameloc] + result[nameloc + 1],
                isvalid=True,
                isAadharNumberValid=Validate(inputAadharNumber),
                doctype="AADHAR",
                validstatus=
                f"The  Card is Validated as Aadhar and It belongs to {fname+lname}"
            )
        else:
            return jsonify(
                inputName=fname + lname,
                nameonCard="Invalid",
                isvalid=False,
                isAadharNumberValid=Validate(inputAadharNumber),
                doctype="AADHAR",
                validstatus=
                f"The Card is a AADHAR Card,The Card does not belong to you, Please Upload valid Card"
            )
    elif val == 2:
        return jsonify(errormsg="Document Uploaded is not Valid")


if __name__ == '__main__':
    app.run(debug=True)
