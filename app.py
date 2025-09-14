from flask import Flask, request, render_template
import os
import cv2
import imutils
from skimage.metrics import structural_similarity
from PIL import Image

# Create app, set template/static folders
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")

# Config paths
app.config['INITIAL_FILE_UPLOADS'] = 'app/static/uploads'
app.config['EXISTNG_FILE'] = 'app/static/original'
app.config['GENERATED_FILE'] = 'app/static/generated'


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    if request.method == "POST":
        # Get uploaded file
        file_upload = request.files['file_upload']

        # Save uploaded image
        uploaded_path = os.path.join(app.config['INITIAL_FILE_UPLOADS'], 'image.jpg')
        uploaded_image = Image.open(file_upload).resize((500, 300)).convert("RGB")
        uploaded_image.save(uploaded_path)

        # Load original image
        original_path = os.path.join(app.config['EXISTNG_FILE'], 'image.jpg')
        original_image = Image.open(original_path).resize((500, 300)).convert("RGB")
        original_image.save(original_path)

        # Convert both to arrays
        original = cv2.imread(original_path)
        uploaded = cv2.imread(uploaded_path)

        # Convert to grayscale
        original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        uploaded_gray = cv2.cvtColor(uploaded, cv2.COLOR_BGR2GRAY)

        # Structural similarity
        (score, diff) = structural_similarity(original_gray, uploaded_gray, full=True)
        diff = (diff * 255).astype("uint8")

        # Threshold + contours
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # Draw rectangles for differences
        for c in cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(original, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.rectangle(uploaded, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # Save outputs
        cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_original.jpg'), original)
        cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_uploaded.jpg'), uploaded)
        cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_diff.jpg'), diff)
        cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_thresh.jpg'), thresh)

        # Status
        result = f"{round(score * 100, 2)}% match"
        status = "⚠ PAN Card Tempered!" if score < 0.9 else "✅ PAN Card is Genuine"

        return render_template("index.html", pred=result, status=status)


if __name__ == "__main__":
    app.run(debug=True)
