# app.py - COMPLETE UPDATED VERSION WITH CHEST X-RAY VALIDATION
from flask import Flask, render_template, request, jsonify, send_file
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import numpy as np
from io import BytesIO
import tensorflow as tf
import base64
import os
import json
import cv2
from skimage import filters, exposure, color, morphology, measure
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pneumonia-detection-secret-key-2024'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# Custom function for grayscale to RGB
def grayscale_to_rgb(x):
    return tf.repeat(x, 3, axis=-1)

# Load model
try:
    model = load_model('pneumonia_model.h5', custom_objects={'grayscale_to_rgb': grayscale_to_rgb})
    print("Model loaded successfully")
except Exception as e:
    print(f"ERROR loading model: {e}")
    model = None

# Import report generator
try:
    from report_generator import report_gen
    report_available = True
    print("Report generator loaded")
except ImportError:
    report_available = False
    print("Report generator not available")

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# CHEST X-RAY VALIDATION FUNCTIONS
def extract_features(img_array):
    features = {}
    try:
        if len(img_array.shape) == 3:
            if img_array.shape[2] == 3:
                gray = color.rgb2gray(img_array)
            else:
                gray = img_array[:,:,0]
        else:
            gray = img_array

        features['mean_intensity'] = np.mean(gray)
        features['std_intensity'] = np.std(gray)
        features['min_intensity'] = np.min(gray)
        features['max_intensity'] = np.max(gray)

        hist, bins = np.histogram(gray, bins=50, range=(0,1))
        features['hist_entropy'] = -np.sum(hist * np.log(hist + 1e-10))
        features['hist_peak'] = np.max(hist)
        features['hist_peak_position'] = np.argmax(hist)

        try:
            gray_uint8 = (gray * 255).astype(np.uint8)
            glcm = graycomatrix(gray_uint8, [1], [0], levels=256, symmetric=True, normed=True)
            features['glcm_contrast'] = graycoprops(glcm, 'contrast')[0,0]
            features['glcm_dissimilarity'] = graycoprops(glcm, 'dissimilarity')[0,0]
            features['glcm_homogeneity'] = graycoprops(glcm, 'homogeneity')[0,0]
            features['glcm_energy'] = graycoprops(glcm, 'energy')[0,0]
            features['glcm_correlation'] = graycoprops(glcm, 'correlation')[0,0]
        except:
            features['glcm_contrast'] = 0
            features['glcm_dissimilarity'] = 0
            features['glcm_homogeneity'] = 0
            features['glcm_energy'] = 0
            features['glcm_correlation'] = 0

        edges = filters.sobel(gray)
        features['edge_mean'] = np.mean(edges)
        features['edge_std'] = np.std(edges)
        features['edge_density'] = np.sum(edges > 0.1) / edges.size

        height, width = gray.shape
        left_lung = gray[:, :width//3]
        right_lung = gray[:, 2*width//3:]
        middle = gray[:, width//3:2*width//3]

        features['left_lung_mean'] = np.mean(left_lung)
        features['right_lung_mean'] = np.mean(right_lung)
        features['middle_mean'] = np.mean(middle)
        features['lung_symmetry'] = abs(features['left_lung_mean'] - features['right_lung_mean'])

        features['aspect_ratio'] = height / width
        features['total_pixels'] = height * width

    except Exception as e:
        print(f"Feature extraction error: {e}")

    return features


def is_chest_xray(img_array, threshold=0.6):
    try:
        features = extract_features(img_array)

        reasons = []
        confidence_score = 0
        total_weight = 0

        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            r = img_array[:,:,0]
            g = img_array[:,:,1]
            b = img_array[:,:,2]
            color_variance = np.mean([np.std(r-g), np.std(g-b), np.std(b-r)])
            if color_variance < 0.05:
                confidence_score += 0.15
                reasons.append("Grayscale image detected")
            else:
                confidence_score -= 0.2
                reasons.append("Color image detected (not typical X-ray)")
        else:
            confidence_score += 0.2
            reasons.append("Single channel grayscale image")
        total_weight += 0.2

        if 0.3 < features.get('mean_intensity', 0) < 0.8:
            confidence_score += 0.15
            reasons.append("Intensity in typical X-ray range")
        else:
            confidence_score -= 0.1
            reasons.append("Unusual brightness for X-ray")
        total_weight += 0.15

        if features.get('std_intensity', 0) > 0.15:
            confidence_score += 0.1
            reasons.append("Good contrast")
        else:
            confidence_score -= 0.1
            reasons.append("Low contrast image")
        total_weight += 0.1

        lung_symmetry = features.get('lung_symmetry', 1)
        if lung_symmetry < 0.15:
            confidence_score += 0.15
            reasons.append("Bilateral symmetry detected")
        else:
            confidence_score -= 0.1
            reasons.append("No bilateral symmetry")
        total_weight += 0.15

        final_confidence = confidence_score / total_weight if total_weight > 0 else 0
        final_confidence = max(0, min(1, final_confidence))

        is_xray = final_confidence >= threshold
        reason_text = ", ".join(reasons[:3])

        return is_xray, final_confidence, reason_text

    except Exception as e:
        print(f"Validation error: {e}")
        return True, 0.5, "Validation inconclusive"


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:

        if model is None:
            return jsonify({'error': 'Model not loaded'}), 500

        file = request.files['image']

        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        file_content = file.read()
        img_original = Image.open(BytesIO(file_content)).convert('RGB')
        img_array = np.array(img_original) / 255.0

        is_xray, xray_confidence, reason = is_chest_xray(img_array)

        if not is_xray:
            return jsonify({
                'error': 'NOT_A_CHEST_XRAY',
                'message': 'The uploaded image does not appear to be a chest X-ray',
                'confidence': f"{xray_confidence*100:.1f}",
                'reason': reason
            }), 400

        img = Image.open(BytesIO(file_content)).convert('L')
        img = img.resize((150, 150))
        img_array_pred = image.img_to_array(img)
        img_array_pred = np.expand_dims(img_array_pred, axis=0) / 255.0

        pred = model.predict(img_array_pred)[0][0]

        result = 'PNEUMONIA' if pred > 0.5 else 'NORMAL'
        confidence = pred if pred > 0.5 else 1 - pred
        confidence_percent = f'{confidence*100:.2f}'

        return jsonify({
            'result': result,
            'confidence': confidence_percent
        })

    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 5MB'}), 413


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


if __name__ == '__main__':

    os.makedirs('uploads', exist_ok=True)
    os.makedirs('static/reports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    print("\n" + "="*60)
    print("Starting Pneumonia Detection App...")
    print("="*60)
    print("Access at: http://localhost:5000")
    print("Reports will be saved in: static/reports/")
    print("Chest X-ray validation: ENABLED")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)