import os
import uuid
from io import BytesIO
from datetime import datetime
from flask import render_template, make_response, url_for, current_app
from xhtml2pdf import pisa
from weasyprint import HTML, CSS
from app import app

def render_to_pdf(template_path, context_data, as_attachment=True):
    """
    Fungsi untuk merender template HTML ke file PDF
    
    Parameters:
    template_path (str): Path ke template HTML
    context_data (dict): Data untuk template
    as_attachment (bool): True untuk download, False untuk inline display
    """
    # Render template HTML dengan data yang diberikan
    rendered_html = render_template(template_path, **context_data)
    
    # Tentukan nama file
    unique_id = uuid.uuid4().hex[:8]
    filename = f'laporan_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{unique_id}.pdf'
    file_path = os.path.join('static', 'pdf', filename)
    absolute_path = os.path.join(current_app.root_path, file_path)
    
    # Konversi HTML ke PDF menggunakan xhtml2pdf
    pdf_io = BytesIO()
    pisa.CreatePDF(rendered_html, dest=pdf_io)
    
    # Simpan PDF ke file sementara (akan terhapus setelah restart server)
    pdf_io.seek(0)
    with open(absolute_path, 'wb') as f:
        f.write(pdf_io.getvalue())
    
    # Jika as_attachment (download), buat response langsung untuk unduhan
    if as_attachment:
        pdf_io.seek(0)
        response = make_response(pdf_io.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    # Jika tidak as_attachment (preview/inline), kembalikan URL publik ke PDF
    return url_for('static', filename=f'pdf/{filename}')

def generate_occupancy_pdf(property_id, start_month, end_month, occupancy_data, property_name, as_attachment=True):
    """
    Generate PDF untuk data hunian
    
    Parameters:
    as_attachment (bool): True untuk download, False untuk inline display
    """
    context = {
        'property_id': property_id,
        'property_name': property_name,
        'start_month': start_month,
        'end_month': end_month,
        'occupancy_data': occupancy_data,
        'current_date': datetime.now().strftime('%d %B %Y'),
        'title': 'Laporan Data Hunian'
    }
    
    return render_to_pdf('pdf/occupancy_report.html', context, as_attachment=as_attachment)

def generate_finance_pdf(property_id, start_date, end_date, finance_data, property_name, summary_data, as_attachment=True):
    """
    Generate PDF untuk data keuangan
    
    Parameters:
    as_attachment (bool): True untuk download, False untuk inline display
    """
    context = {
        'property_id': property_id,
        'property_name': property_name,
        'start_date': start_date,
        'end_date': end_date,
        'finance_data': finance_data,
        'summary_data': summary_data,
        'current_date': datetime.now().strftime('%d %B %Y'),
        'title': 'Laporan Keuangan'
    }
    
    return render_to_pdf('pdf/finance_report.html', context, as_attachment=as_attachment)

def generate_room_stats_pdf(property_id, month, stats_data, property_name, as_attachment=True):
    """
    Generate PDF untuk statistik kamar
    
    Parameters:
    as_attachment (bool): True untuk download, False untuk inline display
    """
    context = {
        'property_id': property_id,
        'property_name': property_name,
        'month': month,
        'stats_data': stats_data,
        'current_date': datetime.now().strftime('%d %B %Y'),
        'title': 'Laporan Statistik Kamar'
    }
    
    return render_to_pdf('pdf/room_stats_report.html', context, as_attachment=as_attachment)

def generate_financial_stats_pdf(property_id, year, stats_data, property_name, as_attachment=True):
    """
    Generate PDF untuk statistik keuangan
    
    Parameters:
    as_attachment (bool): True untuk download, False untuk inline display
    """
    context = {
        'property_id': property_id,
        'property_name': property_name,
        'year': year,
        'stats_data': stats_data,
        'current_date': datetime.now().strftime('%d %B %Y'),
        'title': 'Laporan Statistik Keuangan'
    }
    
    return render_to_pdf('pdf/financial_stats_report.html', context, as_attachment=as_attachment)