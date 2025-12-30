import os
import zipfile
import io
import shutil
import random
import base64
import gc
from PIL import Image, ImageChops, ImageOps
from flask import Flask, render_template, request, send_file, jsonify
from image_processor import process_image, get_random_string

app = Flask(__name__)

# Constants
UPLOAD_FOLDER = './uploads'
CLEAN_FOLDER = './clean_images_web'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEAN_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_directories():
    """Clean up temp folders before new process"""
    for folder in [UPLOAD_FOLDER, CLEAN_FOLDER]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    clean_directories()
    
    if 'files[]' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('files[]')
    keywords_str = request.form.get('keywords', '')
    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
    target_count = int(request.form.get('target_count', 10))
    
    if not keywords:
        keywords = ["default"]

    # 1. Save all uploaded files first
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            saved_files.append(filename)

    if not saved_files:
         return jsonify({'error': 'No valid files uploaded'}), 400

    processed_count = 0
    report_data = []
    
    import pandas as pd 
    
    # 2. Generate target_count images using random source files
    for i in range(target_count):
        # Select a random source image
        src_filename = random.choice(saved_files)
        src_path = os.path.join(UPLOAD_FOLDER, src_filename)
        
        # Key generation
        keyword = keywords[i % len(keywords)]
        new_filename = f"{keyword}_{get_random_string()}.jpg"
        dst_path = os.path.join(CLEAN_FOLDER, new_filename)
        
        if process_image(src_path, dst_path):
            processed_count += 1
            report_data.append({
                '원본파일': src_filename,
                '세탁된파일': new_filename,
                '키워드': keyword,
                '추천_ALT태그': f"{keyword} 관련 이미지 자료"
            })
        
        # Explicit garbage collection after each image
        gc.collect()

    if processed_count == 0:
         return jsonify({'error': 'No files processed'}), 400

    # Create Excel
    df = pd.DataFrame(report_data)
    excel_path = os.path.join(CLEAN_FOLDER, 'image_mapping_list.xlsx')
    df.to_excel(excel_path, index=False)

    # Create Zip directly on disk (No Memory Buffer)
    zip_path = os.path.join(CLEAN_FOLDER, 'processed_images.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(CLEAN_FOLDER):
            for file in files:
                # Avoid zipping the zip itself if it exists (though we cleared folder)
                if file != 'processed_images.zip':
                    zf.write(os.path.join(root, file), file)

    return jsonify({'message': 'Success', 'count': processed_count, 'download_url': '/download/processed_images.zip'})

@app.route('/compare', methods=['POST'])
def compare_images():
    if 'fileA' not in request.files or 'fileB' not in request.files:
        return jsonify({'error': 'Missing files'}), 400
    
    fileA = request.files['fileA']
    fileB = request.files['fileB']
    
    # helper to process
    def get_image_info(file_obj):
        file_obj.seek(0, os.SEEK_END)
        size = file_obj.tell()
        file_obj.seek(0)
        img = Image.open(file_obj)
        # Check Exif
        has_metadata = "Present" if img.getexif() else "Clean"
        return img, size, has_metadata, img.size

    imgA, sizeA, metaA, dimA = get_image_info(fileA)
    imgB, sizeB, metaB, dimB = get_image_info(fileB)
    
    # Visual Difference
    # Resize B to match A for difference calculation if needed, or just min size
    target_size = imgA.size
    imgB_resized = imgB.resize(target_size)
    if imgA.mode != imgB_resized.mode:
        imgB_resized = imgB_resized.convert(imgA.mode)
        
    diff = ImageChops.difference(imgA, imgB_resized)
    # Invert to make differences white on black, easier to see? Or just enhance.
    # Actually ImageChops.difference gives absolute difference. 
    # Let's invert it so unchanged pixels are white, changed are colored/black? 
    # User asked for "Visual Difference (Heatmap)".
    # Let's just create a strong contrast version.
    if diff.getbbox():
        diff = ImageOps.invert(diff) # Invert so background is white, changes are colored
    else:
        # Identical
        diff = Image.new('RGB', target_size, (255, 255, 255))
        
    # Save diff to base64
    buffered = io.BytesIO()
    diff.save(buffered, format="JPEG")
    diff_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return jsonify({
        'metaA': metaA, 'metaB': metaB,
        'sizeA': f"{sizeA/1024:.1f} KB", 'sizeB': f"{sizeB/1024:.1f} KB",
        'dimA': f"{dimA[0]}x{dimA[1]}", 'dimB': f"{dimB[0]}x{dimB[1]}",
        'diffImage': f"data:image/jpeg;base64,{diff_b64}"
    })

@app.route('/download/<path:filename>')
def download(filename):
    return send_file(os.path.join(CLEAN_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
