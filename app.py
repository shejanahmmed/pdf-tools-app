from flask import Flask, render_template, request, send_file
from PyPDF2 import PdfMerger
from docx2pdf import convert
from pdf2image import convert_from_path
from PIL import Image
import os
import uuid
import io
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge', methods=['GET', 'POST'])
def merge():
    if request.method == 'POST':
        files = request.files.getlist('pdfs')
        filename_input = request.form.get('filename', 'merged').strip() or 'merged'
        paths = []
        for f in files:
            path = os.path.join(UPLOAD_FOLDER, f.filename)
            f.save(path)
            paths.append(path)

        output_path = os.path.join(UPLOAD_FOLDER, f'{filename_input}.pdf')
        merger = PdfMerger()
        for pdf in paths:
            merger.append(pdf)
        merger.write(output_path)
        merger.close()

        for f in paths:
            os.remove(f)

        return send_file(output_path, download_name=f'{filename_input}.pdf', as_attachment=True)
    return render_template('merge.html')

@app.route('/doc2pdf', methods=['GET', 'POST'])
def doc_to_pdf():
    if request.method == 'POST':
        file = request.files['docx']
        filename_input = request.form.get('filename', 'converted').strip() or 'converted'
        input_path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".docx")
        output_path = os.path.join(UPLOAD_FOLDER, f"{filename_input}.pdf")
        file.save(input_path)
        convert(input_path, output_path)
        os.remove(input_path)
        return send_file(output_path, download_name=f'{filename_input}.pdf', as_attachment=True)
    return render_template('doc2pdf.html')

@app.route('/img2pdf', methods=['GET', 'POST'])
def img_to_pdf():
    if request.method == 'POST':
        files = request.files.getlist('images')
        filename_input = request.form.get('filename', 'output').strip() or 'output'
        images = [Image.open(f.stream).convert('RGB') for f in files]
        output_path = os.path.join(UPLOAD_FOLDER, f'{filename_input}.pdf')
        images[0].save(output_path, save_all=True, append_images=images[1:])
        return send_file(output_path, download_name=f'{filename_input}.pdf', as_attachment=True)
    return render_template('img2pdf.html')

@app.route('/pdf2img', methods=['GET', 'POST'])
def pdf_to_img():
    if request.method == 'POST':
        pdf_file = request.files['pdf']
        filename_input = request.form.get('filename', 'pdf_pages').strip() or 'pdf_pages'
        path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
        pdf_file.save(path)

        poppler_path = None  # Adjust if poppler is not in PATH

        images = convert_from_path(path, poppler_path=poppler_path)
        os.remove(path)

        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, 'w') as z:
            for i, img in enumerate(images):
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                z.writestr(f'page_{i+1}.png', img_bytes.getvalue())
        mem_zip.seek(0)

        return send_file(mem_zip, download_name=f'{filename_input}.zip', as_attachment=True)
    return render_template('pdf2img.html')

if __name__ == '__main__':
    app.run(debug=True)
