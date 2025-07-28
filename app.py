import io
import requests
from flask import Flask, request, jsonify
from pdf2image import convert_from_bytes, convert_from_path
from PIL import Image
import pytesseract
import tempfile
import os

app = Flask(__name__)

@app.route('/ocr', methods=['POST'])
def ocr_from_url():
    # This endpoint still handles URLs as before
    data = request.get_json(silent=True)
    if not data or 'url' not in data:
        return jsonify({"error": "Missing 'url' in JSON body"}), 400

    image_url = data['url']
    lang = data.get('lang', 'eng') # Default to English, or 'auto' for auto-detection

    try:
        response = requests.get(image_url)
        response.raise_for_status() # Raise an exception for bad status codes
        file_content = response.content

        # Determine file type and process
        if image_url.lower().endswith(('.pdf')):
            # For PDFs, convert to images first
            with tempfile.TemporaryDirectory() as path:
                # pdf2image needs the PDF to be on disk, so we save it temporarily
                temp_pdf_path = os.path.join(path, 'temp.pdf')
                with open(temp_pdf_path, 'wb') as f:
                    f.write(file_content)

                images = convert_from_path(temp_pdf_path)
                text = ""
                for i, image in enumerate(images):
                    # Use Pillow's save method for image and then Tesseract
                    # Ensure we convert to RGB as Tesseract prefers it for certain image types
                    text += pytesseract.image_to_string(image.convert('RGB'), lang=lang) + "\n"
        else:
            # For images, process directly
            image = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(image.convert('RGB'), lang=lang)

        return jsonify({"success": True, "text": text})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error fetching URL: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"OCR processing failed: {e}"}), 500


@app.route('/upload_and_ocr', methods=['POST'])
def upload_and_ocr():
    # This new endpoint handles file uploads
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    lang = request.form.get('lang', 'auto') # Get language from form data

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Read the file content directly from the FileStorage object
        file_content = file.read()
        filename = file.filename

        try:
            # Determine file type based on filename extension
            if filename.lower().endswith(('.pdf')):
                # For PDFs, convert to images first
                with tempfile.TemporaryDirectory() as path:
                    # pdf2image needs the PDF to be on disk, so we save it temporarily
                    temp_pdf_path = os.path.join(path, filename)
                    with open(temp_pdf_path, 'wb') as f:
                        f.write(file_content)

                    images = convert_from_path(temp_pdf_path)
                    text = ""
                    for i, image in enumerate(images):
                        text += pytesseract.image_to_string(image.convert('RGB'), lang=lang) + "\n"
            else:
                # For images, process directly
                image = Image.open(io.BytesIO(file_content))
                text = pytesseract.image_to_string(image.convert('RGB'), lang=lang)

            return jsonify({"success": True, "text": text})

        except Exception as e:
            return jsonify({"error": f"OCR processing failed: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 8000))
