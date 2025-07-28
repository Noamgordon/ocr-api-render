import os
import requests
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import io

app = Flask(__name__)

# Function to get Tesseract language code for auto-detection
def get_tesseract_lang_code(lang_hint="auto"):
    if lang_hint == "auto":
        # Tesseract can use '+' for multiple languages to try and auto-detect
        # 'eng' for English, 'heb' for Hebrew. Add others if you expect them.
        return "eng+heb"
    elif lang_hint == "hebrew":
        return "heb"
    elif lang_hint == "english":
        return "eng"
    # Add more language mappings here if needed (e.g., "spanish": "spa")
    else:
        return lang_hint # Assume valid Tesseract code if not in specific mapping

@app.route('/ocr', methods=['POST'])
def ocr_from_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Please provide a 'url' in the JSON body."}), 400

    file_url = data['url']
    lang_hint = data.get('lang', 'auto').lower() # Default to auto-detect

    try:
        response = requests.get(file_url, stream=True)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        file_content = io.BytesIO(response.content)
        extracted_texts = []
        is_pdf = False

        # Basic check for PDF by content type or file extension.
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/pdf' in content_type or file_url.lower().endswith('.pdf'):
            is_pdf = True

        if is_pdf:
            # For PDFs, convert each page to an image and then OCR
            # `poppler_path` is usually not needed when poppler-utils is system-installed in Docker
            images = convert_from_bytes(file_content.read(), dpi=300) # Increased DPI for better accuracy

            tess_lang = get_tesseract_lang_code(lang_hint)

            for i, image in enumerate(images):
                # Perform OCR on each image
                # config='--psm 3' is default for 'fully automatic page segmentation, but no OSD.'
                text = pytesseract.image_to_string(image, lang=tess_lang)
                extracted_texts.append(f"--- Page {i+1} ---\n{text.strip()}")
        else:
            # For images, just open and OCR
            image = Image.open(file_content)

            tess_lang = get_tesseract_lang_code(lang_hint)

            text = pytesseract.image_to_string(image, lang=tess_lang)
            extracted_texts.append(text.strip())

        if not extracted_texts:
            return jsonify({"status": "success", "message": "No text found or unable to process file."}), 200

        full_text = "\n\n".join(extracted_texts)

        return jsonify({"status": "success", "text": full_text}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to download file from URL: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred during OCR processing: {e}"}), 500

if __name__ == '__main__':
    # This runs the Flask development server (not used on Render directly)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))