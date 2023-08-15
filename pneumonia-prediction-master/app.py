import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import numpy as np
import tensorflow as tf
from PIL import Image


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg"}

# Load the TensorFlow Lite model
interpreter = tf.lite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

# Image dimensions
img_width, img_height = 150, 150

# Function to preprocess the uploaded image
def preprocess_image(image_path):
    img = tf.keras.preprocessing.image.load_img(image_path, target_size=(img_width, img_height))
    img = tf.keras.preprocessing.image.img_to_array(img) / 255.0
    img = np.expand_dims(img, axis=0)
    return img

# Function to check if the file has an allowed extension
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Handle file upload
        file = request.files["file"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            # Preprocess the image
            img = preprocess_image(file_path)

            # Run inference on the TensorFlow Lite model
            input_index = interpreter.get_input_details()[0]["index"]
            output_index = interpreter.get_output_details()[0]["index"]
            interpreter.set_tensor(input_index, img)
            interpreter.invoke()
            prediction = interpreter.get_tensor(output_index)

            result = "Pneumonia" if prediction[0][0] > 0.5 else "Normal"

            return redirect(url_for("result", result=result, image_path=file_path))

    return render_template("index.html")

@app.route("/result")
def result():
    result = request.args.get("result")
    image_path = request.args.get("image_path")
    return render_template("result.html", result=result, image_path=image_path)

port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
