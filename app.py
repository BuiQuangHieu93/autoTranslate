import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
from googletrans import Translator, LANGUAGES

app = Flask(__name__)
CORS(app)

# Ensure the Tesseract command is found, set the Tesseract command path if needed
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update with your Tesseract path

translator = Translator()

def get_font_size(draw, boxes):
    # Calculate the average height of characters
    total_height = sum([bh for _, _, _, bh in boxes])
    average_height = total_height / len(boxes)

    # Choose a font size based on the average height of characters
    font_size = int(average_height * 1.4)  # Adjust as needed
    return ImageFont.truetype("arial.ttf", font_size)

def wrap_text(text, font, max_width):
    """Wrap text to fit within a given width when rendered."""
    lines = []
    words = text.split()
    current_line = ''
    for word in words:
        # Measure the width of the text with getbbox()
        temp_line = current_line + (word + ' ')
        temp_line_width = font.getbbox(temp_line)[2]
        if temp_line_width <= max_width:
            current_line = temp_line
        else:
            lines.append(current_line)
            current_line = word + ' '
    if current_line:
        lines.append(current_line)
    return '\n'.join(lines)

@app.route('/translate_and_replace', methods=['POST'])
def translate_and_replace():
    file = request.files['file']
    target_lang = request.form['target_lang']
    
    if target_lang not in LANGUAGES:
        return jsonify({"error": "Invalid target language"}), 400
    
    if file:
        # Read image file
        img = Image.open(io.BytesIO(file.read()))
        img = img.convert('RGB')
        img_np = np.array(img)
        
        # Convert to grayscale
        gray_img = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

        # Perform OCR
        data = pytesseract.image_to_data(gray_img, output_type=pytesseract.Output.DICT)
        
        # Check if 'text' and other keys are present and not None
        if not data or 'text' not in data or data['text'] is None:
            return jsonify({"error": "OCR failed or no text detected"}), 400

        draw = ImageDraw.Draw(img)

        # Initialize variables to combine words into sentences
        combined_text = ""
        combined_boxes = []
        last_y = None

        for i in range(len(data['text'])):
            text = data['text'][i]
            if text and int(data['conf'][i]) > 0:  # Filter out weak OCR results
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

                # Check vertical distance condition
                if last_y is not None and abs(y - last_y) > 35:
                    if combined_text.strip():
                        try:
                            # Translate the combined text
                            translated_text = translator.translate(combined_text, dest=target_lang).text
                        except Exception as e:
                            translated_text = combined_text
                            print(f"Translation error: {e}")
                        if translated_text is None:
                            translated_text = combined_text

                        # Calculate the bounding box for the translated text
                        max_x = max([bx + bw for bx, by, bw, bh in combined_boxes])
                        max_y = max([by + bh for bx, by, bw, bh in combined_boxes])
                        min_x = min([bx for bx, by, bw, bh in combined_boxes])
                        min_y = min([by for bx, by, bw, bh in combined_boxes])

                        # Get the appropriate font size
                        translated_font = get_font_size(draw, combined_boxes)
                        
                        # Wrap the translated text
                        wrapped_text = wrap_text(translated_text, translated_font, max_x - min_x)

                        # Draw a white rectangle over the original text
                        draw.rectangle([(min_x, min_y), (max_x, max_y)], fill='white')

                        # Draw the translated text on the image
                        draw.text((min_x, min_y), wrapped_text, fill='black', font=translated_font)

                    # Reset combined text and boxes for the next sentence
                    combined_text = ""
                    combined_boxes = []

                if combined_text:
                    combined_text += " " + text
                else:
                    combined_text = text
                
                combined_boxes.append((x, y, w, h))
                last_y = y

                # Check if the current text ends with a period
                if text.endswith('.'):
                    if combined_text.strip():
                        try:
                            # Translate the combined text
                            translated_text = translator.translate(combined_text, dest=target_lang).text
                        except Exception as e:
                            translated_text = combined_text
                            print(f"Translation error: {e}")
                        if translated_text is None:
                            translated_text = combined_text

                        # Calculate the bounding box for the translated text
                        max_x = max([bx + bw for bx, by, bw, bh in combined_boxes])
                        max_y = max([by + bh for bx, by, bw, bh in combined_boxes])
                        min_x = min([bx for bx, by, bw, bh in combined_boxes])
                        min_y = min([by for bx, by, bw, bh in combined_boxes])

                        # Get the appropriate font size
                        translated_font = get_font_size(draw, combined_boxes)
                        
                        # Wrap the translated text
                        wrapped_text = wrap_text(translated_text, translated_font, max_x - min_x)

                        # Draw a white rectangle over the original text
                        draw.rectangle([(min_x, min_y), (max_x, max_y)], fill='white')

                        # Draw the translated text on the image
                        draw.text((min_x, min_y), wrapped_text, fill='black', font=translated_font)

                    # Reset combined text and boxes for the next sentence
                    combined_text = ""
                    combined_boxes = []

        # Handle any remaining combined text (if not ended with a period)
        if combined_text.strip():
            try:
                translated_text = translator.translate(combined_text, dest=target_lang).text
            except Exception as e:
                translated_text = combined_text
                print(f"Translation error: {e}")
            if translated_text is None:
                translated_text = combined_text

            # Calculate the bounding box for the translated text
            max_x = max([bx + bw for bx, by, bw, bh in combined_boxes])
            max_y = max([by + bh for bx, by, bw, bh in combined_boxes])
            min_x = min([bx for bx, by, bw, bh in combined_boxes])
            min_y = min([by for bx, by, bw, bh in combined_boxes])

            # Get the appropriate font size
            translated_font = get_font_size(draw, combined_boxes)
            
            # Wrap the translated text
            wrapped_text = wrap_text(translated_text, translated_font, max_x - min_x)

            # Draw a white rectangle over the original text
            draw.rectangle([(min_x, min_y), (max_x, max_y)], fill='white')

            # Draw the translated text on the image
            draw.text((min_x, min_y), wrapped_text, fill='black', font=translated_font)

        # Save the modified image to a buffer
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        return jsonify({"image": img_buffer.getvalue().hex()})
    return jsonify({"error": "No file uploaded"}), 400

if __name__ == '__main__':
    app.run(debug=True)
