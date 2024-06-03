from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
from googletrans import Translator, LANGUAGES
from skimage import filters
from skimage.morphology import skeletonize
from scipy.ndimage import interpolation as inter

app = Flask(__name__)
CORS(app)

# Ensure the Tesseract command is found, set the Tesseract command path if needed
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update with your Tesseract path

translator = Translator()

def check_collision(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    if x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2:
        return True
    return False

def split_text_into_lines(text, font, max_width):
    lines = []
    words = text.split()
    current_line = ''
    for word in words:
        # Calculate the width of the current line with the new word
        temp_line = current_line + (word + ' ')
        temp_mask = font.getmask(temp_line)
        temp_line_width, _ = temp_mask.size
        # If the width exceeds the maximum width, start a new line
        if temp_line_width <= max_width:
            current_line = temp_line
        else:
            lines.append(current_line)
            current_line = word + ' '
    # Add the last line
    lines.append(current_line)
    return lines

def preprocess_image(file):
    if file:
        img = Image.open(io.BytesIO(file.read()))
        img = img.convert('RGB')
        img_np = np.array(img)

        # Convert to grayscale
        gray_img = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

        # Use pytesseract to do OCR on the preprocessed image
        data = pytesseract.image_to_data(gray_img, output_type=pytesseract.Output.DICT)
        
        return img, data


@app.route('/translate_and_replace', methods=['POST'])
def translate_and_replace():
    file = request.files['file']
    target_lang = request.form['target_lang']
    
    if target_lang not in LANGUAGES:
        return jsonify({"error": "Invalid target language"}), 400
    
   
    img, data = preprocess_image(file)
        
    if not data or 'text' not in data or data['text'] is None:
        return jsonify({"error": "OCR failed or no text detected"}), 400

    draw = ImageDraw.Draw(img)
    word_positions = []

    # Collect word positions and adjust bounding boxes
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if text and int(data['conf'][i]) > 0:
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            adjusted_box = (x - 10, y - 10, w + 20, h + 20)  # Increase box size
            word_positions.append((text, adjusted_box))
            print(f"{text} - Original: ({x}, {y}, {w}, {h}), Adjusted: {adjusted_box}")

    # Check for collisions and group related words
    groups = []
    for i in range(len(word_positions)):
        found = False
        for group in groups:
            if any(check_collision(word_positions[i][1], word_positions[j][1]) for j in group):
                group.append(i)
                found = True
                break
        if not found:
            groups.append([i])

    # Calculate average height of text in the box
    average_height = sum(h for _, (_, _, _, h) in word_positions) / len(word_positions)
    fontsize = int(average_height * 0.6)
    font = ImageFont.truetype("arial.ttf", fontsize)
    print("average_height", average_height)

    # Draw boxes around groups of colliding words
    for group in groups:
        if len(group) > 1:  # Only draw if there are collisions
            min_x = min(word_positions[i][1][0] for i in group)
            min_y = min(word_positions[i][1][1] for i in group)
            max_x = max(word_positions[i][1][0] + word_positions[i][1][2] for i in group)
            max_y = max(word_positions[i][1][1] + word_positions[i][1][3] for i in group)
    
            # Sort words left to right, top to bottom
            group_sorted = sorted(group, key=lambda i: (word_positions[i][1][1], word_positions[i][1][0]))
            sentence = " ".join(word_positions[i][0] for i in group_sorted)
            
            # Translate sentence
            translated_sentence = translator.translate(sentence, dest=target_lang).text

            draw.rectangle([min_x, min_y, max_x, max_y], outline="red", width=2)
            draw.rectangle([min_x, min_y, max_x, max_y], fill="white")  # White out the original text

            translated_lines = split_text_into_lines(translated_sentence, font, max_x - min_x)

            y_text = min_y
            for line in translated_lines:
                draw.text((min_x, y_text), line, fill="black", font=font)
                # Move to the next line by using the ascent and descent values of the font
                ascent, descent = font.getmetrics()
                y_text += ascent + descent
          
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    return jsonify({"image": img_buffer.getvalue().hex()})

if __name__ == '__main__':
    app.run(debug=True)
