# report_generator.py
import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import base64
from io import BytesIO

class PneumoniaReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.report_folder = 'static/reports'
        
        # Create reports directory if not exists
        os.makedirs(self.report_folder, exist_ok=True)
        
    def create_patient_info_table(self, patient_info):
        """Patient information table create karta hai"""
        patient_data = [
            ['Patient Name:', patient_info.get('name', 'N/A')],
            ['Patient Age:', str(patient_info.get('age', 'N/A'))],
            ['Patient ID:', patient_info.get('id', 'N/A')],
            ['Gender:', patient_info.get('gender', 'N/A')],
            ['Report Date:', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ['Referring Physician:', patient_info.get('physician', 'Dr. Smith')]
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 3*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        
        return patient_table
    
    def create_diagnosis_section(self, prediction_result, confidence):
        """Diagnosis section create karta hai"""
        is_pneumonia = prediction_result == "PNEUMONIA"
        
        diagnosis_style = ParagraphStyle(
            'DiagnosisStyle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#dc2626') if is_pneumonia else colors.HexColor('#059669'),
            spaceAfter=12,
            alignment=1
        )
        
        diagnosis_text = f"DIAGNOSIS: {prediction_result}"
        diagnosis_para = Paragraph(diagnosis_text, diagnosis_style)
        
        confidence_text = f"AI Confidence Level: {confidence}%"
        confidence_para = Paragraph(confidence_text, self.styles['Normal'])
        
        return diagnosis_para, confidence_para
    
    def create_clinical_findings(self, prediction_result, confidence):
        """Clinical findings section create karta hai"""
        is_pneumonia = prediction_result == "PNEUMONIA"
        
        findings_style = ParagraphStyle(
            'FindingsStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.HexColor('#374151')
        )
        
        if is_pneumonia:
            findings = [
                "AI model detected radiographic signs consistent with pneumonia",
                f"Detection confidence level: {confidence}%",
                "Presence of pulmonary infiltrates/consolidation observed",
                "Opacification in lung fields visible",
                "Air bronchograms may be present",
                "Requires immediate clinical correlation"
            ]
        else:
            findings = [
                "No radiographic evidence of pneumonia detected",
                f"Normal findings confidence: {confidence}%",
                "Clear lung fields with normal pulmonary markings",
                "No significant consolidation or infiltrates",
                "Normal cardiomediastinal silhouette",
                "Routine follow-up recommended"
            ]
        
        findings_paras = []
        for finding in findings:
            findings_paras.append(Paragraph(finding, findings_style))
        
        return findings_paras
    
    def create_recommendations(self, prediction_result):
        """Medical recommendations create karta hai"""
        is_pneumonia = prediction_result == "PNEUMONIA"
        
        rec_style = ParagraphStyle(
            'RecommendationStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.HexColor('#374151')
        )
        
        if is_pneumonia:
            recommendations = [
                "IMMEDIATE consultation with pulmonologist or primary care physician",
                "Complete Blood Count (CBC) and inflammatory markers testing",
                "Consider empirical antibiotic therapy based on clinical assessment",
                "Chest CT scan for detailed evaluation if clinically indicated",
                "Monitor oxygen saturation and respiratory status closely",
                "Follow-up chest X-ray in 48-72 hours to assess treatment response",
                "Hospital admission if signs of respiratory distress present"
            ]
        else:
            recommendations = [
                "Routine health maintenance and monitoring",
                "Follow-up as per standard clinical practice",
                "Maintain good respiratory hygiene practices",
                "Seek medical attention if respiratory symptoms develop",
                "Annual health check-up recommended",
                "Smoking cessation advised if applicable",
                "Vaccination status review (pneumococcal, influenza)"
            ]
        
        rec_paras = []
        for recommendation in recommendations:
            rec_paras.append(Paragraph(recommendation, rec_style))
        
        return rec_paras
    
    def add_header_footer(self, canvas, doc):
        """PDF header aur footer add karta hai"""
        canvas.saveState()
        
        # Header
        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(colors.HexColor('#6366f1'))
        canvas.drawString(inch, 10.5*inch, "PneumoScan AI - Medical Imaging Report")
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(inch, 0.5*inch, f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        canvas.drawRightString(7.5*inch, 0.5*inch, "Page %d" % doc.page)
        
        canvas.restoreState()
    
    def generate_report(self, patient_info, prediction_result, confidence, image_data=None, output_path=None):
        """Complete PDF report generate karta hai"""
        
        if output_path is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            patient_id = patient_info.get('id', 'unknown').replace(' ', '_')
            output_path = f"{self.report_folder}/pneumonia_report_{patient_id}_{timestamp}.pdf"
        
        # PDF document create karein
        doc = SimpleDocTemplate(output_path, pagesize=letter, 
                              topMargin=1.5*inch, bottomMargin=1*inch)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
            alignment=1
        )
        title = Paragraph("CHEST X-RAY AI ANALYSIS REPORT", title_style)
        story.append(title)
        
        # Patient Information
        story.append(Paragraph("PATIENT INFORMATION", self.styles['Heading2']))
        story.append(Spacer(1, 12))
        story.append(self.create_patient_info_table(patient_info))
        story.append(Spacer(1, 20))
        
        # Diagnosis Results
        story.append(Paragraph("DIAGNOSTIC FINDINGS", self.styles['Heading2']))
        story.append(Spacer(1, 12))
        
        diagnosis_para, confidence_para = self.create_diagnosis_section(prediction_result, confidence)
        story.append(diagnosis_para)
        story.append(confidence_para)
        story.append(Spacer(1, 15))
        
        # Clinical Findings
        story.append(Paragraph("CLINICAL FINDINGS", self.styles['Heading2']))
        story.append(Spacer(1, 10))
        
        findings = self.create_clinical_findings(prediction_result, confidence)
        for finding in findings:
            story.append(finding)
        
        story.append(Spacer(1, 15))
        
        # Medical Recommendations
        story.append(Paragraph("MEDICAL RECOMMENDATIONS", self.styles['Heading2']))
        story.append(Spacer(1, 10))
        
        recommendations = self.create_recommendations(prediction_result)
        for recommendation in recommendations:
            story.append(recommendation)
        
        story.append(Spacer(1, 20))
        
        # X-Ray Image (agar available ho)
        if image_data:
            try:
                story.append(Paragraph("X-RAY IMAGE", self.styles['Heading2']))
                story.append(Spacer(1, 10))
                
                # Convert base64 to image
                if isinstance(image_data, str) and image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                
                img_buffer = BytesIO(base64.b64decode(image_data))
                img = Image(img_buffer, width=4*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 15))
            except Exception as e:
                print(f"ERROR Image add karne mein error: {e}")
        
        # Disclaimer
        disclaimer_style = ParagraphStyle(
            'DisclaimerStyle',
            parent=self.styles['Italic'],
            fontSize=8,
            textColor=colors.HexColor('#64748b'),
            spaceBefore=20
        )
        
        disclaimer_text = """
        IMPORTANT DISCLAIMER: This AI analysis is intended for informational purposes only and should not be used as a substitute for professional medical advice, diagnosis, or treatment. 
        This report has been generated by an artificial intelligence system and requires verification by a qualified healthcare professional. 
        Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.
        """
        
        disclaimer = Paragraph(disclaimer_text, disclaimer_style)
        story.append(disclaimer)
        
        # PDF build karein with header footer
        doc.build(story, onFirstPage=self.add_header_footer, onLaterPages=self.add_header_footer)
        
        print(f"OK PDF Report Generated: {output_path}")
        return output_path

# Global instance
report_gen = PneumoniaReportGenerator()

