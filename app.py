import io
import base64
from flask import Flask, render_template, request, send_file
from PIL import Image as PILImage, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

app = Flask(__name__)

def crop_image_to_buffer(base64_str, target_w=490, target_h=410):
    if ',' in base64_str:
        base64_str = base64_str.split(',', 1)[1]
    img_bytes = base64.b64decode(base64_str)
    img = PILImage.open(io.BytesIO(img_bytes)).convert('RGB')
    img_cropped = ImageOps.fit(img, (target_w, target_h), method=PILImage.Resampling.LANCZOS)
    
    buf = io.BytesIO()
    img_cropped.save(buf, format='JPEG', quality=92)
    buf.seek(0)
    return buf

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    data = request.json
    judul1 = data.get('judul1', 'LAPORAN KEGIATAN')
    judul2 = data.get('judul2', '')
    judul3 = data.get('judul3', '')
    items = data.get('items', [])

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        alignment=TA_CENTER
    )
    ket_style = ParagraphStyle(
        'KetStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT
    )
    no_style = ParagraphStyle(
        'NoStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        alignment=TA_CENTER
    )

    for j in [judul1, judul2, judul3]:
        if j.strip():
            elements.append(Paragraph(j.upper(), title_style))
    elements.append(Spacer(1, 14))

    table_data = [[
        Paragraph('<b>NO</b>', no_style),
        Paragraph('<b>FOTO KEGIATAN</b>', no_style),
        Paragraph('<b>KETERANGAN</b>', no_style)
    ]]

    for idx, item in enumerate(items, start=1):
        img_data = item.get('img', '')
        ket_text = item.get('text', '').replace('\n', '<br/>')

        if img_data:
            img_buf = crop_image_to_buffer(img_data)
            foto_cell = Image(img_buf, width=175, height=146)
        else:
            foto_cell = Paragraph('<font color="gray">(Tidak ada foto)</font>', no_style)

        table_data.append([
            Paragraph(str(idx), no_style),
            foto_cell,
            Paragraph(ket_text, ket_style)
        ])

    col_widths = [43, 250, 230]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFF2CC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (2, 1), (2, -1), 12),
    ]))

    elements.append(table)
    doc.build(elements)

    pdf_buffer.seek(0)
    filename = "".join(c if c.isalnum() else "_" for c in judul1.strip()) + ".pdf"
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5086, debug=False)
