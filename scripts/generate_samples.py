"""Generator for synthetic clearance sample documents (PDF and images)."""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_quit_claim(filepath: str, is_valid: bool = True):
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        alignment=1,  # Center
        fontSize=16,
        spaceAfter=20,
    )

    story.append(Paragraph("<b>RELEASE, WAIVER AND QUITCLAIM</b>", title_style))
    story.append(Spacer(1, 10))

    if is_valid:
        amount_fig = "PHP 52,400.00"
        amount_words = "Fifty Two Thousand Four Hundred Pesos"
        sig_text = "<i>[SIGNED: Juan Dela Cruz]</i>"
    else:
        amount_fig = "PHP 48,500.00"
        amount_words = "Fifty Eight Thousand Five Hundred Pesos"
        sig_text = "<font color='red'>[UNSIGNED / SIGNATURE MISSING]</font>"

    body_text = f"""
    KNOW ALL MEN BY THESE PRESENTS:<br/><br/>
    That I, <b>Juan Dela Cruz</b>, of legal age, Filipino, with Employee ID <b>EMP-94812</b>, 
    formerly employed with the Company until separation date of <b>2026-08-31</b>, do hereby acknowledge receipt of the sum of 
    <b>{amount_words} ({amount_fig})</b>, Philippine Currency, representing full and final settlement of all salaries, 
    separation pay, 13th month pay, and all other benefits due me from the Company.<br/><br/>
    I hereby release, remise, and forever discharge the Company, its directors, officers, agents, and employees 
    from any and all manner of actions, causes of actions, sums of money, accounts, contracts, claims, and demands whatsoever 
    in law or in equity.<br/><br/>
    IN WITNESS WHEREOF, I have hereunto affixed my signature this 31st day of August, 2026 at Taguig City, Philippines.
    """
    story.append(Paragraph(body_text, styles['Normal']))
    story.append(Spacer(1, 30))

    # Signature block
    sig_data = [
        [Paragraph(f"<b>Employee Signature:</b><br/>{sig_text}", styles['Normal']),
         Paragraph("<b>Witness:</b><br/><i>[SIGNED: Maria Clara]</i>", styles['Normal'])],
        [Paragraph("Date: 2026-08-31", styles['Normal']),
         Paragraph("Date: 2026-08-31", styles['Normal'])],
        [Paragraph("<b>Notary Public:</b><br/>Atty. Jose Rizal, Notary Public for Taguig City", styles['Normal']),
         Paragraph("Commission No. 2026-88<br/>Roll No. 44102", styles['Normal'])]
    ]
    t = Table(sig_data, colWidths=[260, 260])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t)
    doc.build(story)


def generate_bank_proof_image(filepath: str, is_valid: bool = True):
    img = Image.new("RGB", (600, 400), color=(240, 245, 255))
    draw = ImageDraw.Draw(img)

    # Banner
    draw.rectangle([(0, 0), (600, 60)], fill=(0, 102, 204))
    draw.text((20, 18), "GCASH ACCOUNT VERIFICATION & ENROLLMENT", fill=(255, 255, 255))

    acc_num = "0917-987-6543" if is_valid else "0917-12"
    acc_holder = "Juan Dela Cruz"
    status_text = "VERIFIED USER" if is_valid else "INCOMPLETE / UNVERIFIED"

    # Info card
    draw.rectangle([(30, 80), (570, 360)], fill=(255, 255, 255), outline=(200, 210, 230), width=2)
    draw.text((50, 100), f"Account Holder: {acc_holder}", fill=(30, 30, 30))
    draw.text((50, 140), f"Mobile / Account No: {acc_num}", fill=(0, 50, 180))
    draw.text((50, 180), f"Account Type: GCash Personal Wallet", fill=(50, 50, 50))
    draw.text((50, 220), f"KYC Status: {status_text}", fill=(0, 150, 50) if is_valid else (200, 0, 0))

    # Mock QR code box
    draw.rectangle([(420, 100), (540, 220)], fill=(230, 230, 230), outline=(100, 100, 100))
    draw.text((435, 150), "[ QR CODE ]", fill=(100, 100, 100))

    draw.text((50, 300), "Official Payroll Disbursement Proof - Generated via Mobile App", fill=(120, 120, 120))
    img.save(filepath)


def generate_clearance_sheet(filepath: str, is_valid: bool = True):
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('ClrTitle', parent=styles['Heading1'], alignment=1, fontSize=16, spaceAfter=15)
    story.append(Paragraph("<b>EMPLOYEE CLEARANCE SIGN-OFF SHEET</b>", title_style))
    story.append(Paragraph("<b>Employee Name:</b> Juan Dela Cruz &nbsp;&nbsp;&nbsp;&nbsp; <b>ID:</b> EMP-94812 &nbsp;&nbsp;&nbsp;&nbsp; <b>Separation Date:</b> 2026-08-31", styles['Normal']))
    story.append(Spacer(1, 15))

    it_status = "CLEARED" if is_valid else "PENDING / ON HOLD"
    it_sig = "Alex Tan (SIGNED)" if is_valid else "<font color='red'>[SIGNATURE MISSING]</font>"
    it_notes = "All IT assets returned in good condition" if is_valid else "HOLD: Unreturned ThinkPad T14 & Monitor"
    it_date = "2026-09-02" if is_valid else ""

    table_data = [
        ["Department", "Status", "Accountability Notes", "Approver Name & Signature", "Date"],
        ["Information Technology (IT)", Paragraph(f"<b>{it_status}</b>", styles['Normal']), Paragraph(it_notes, styles['Normal']), Paragraph(it_sig, styles['Normal']), it_date],
        ["Administration & Facilities", "CLEARED", "Access badge & keys surrendered", "Elena Cruz (SIGNED)", "2026-09-02"],
        ["Finance & Accounting", "CLEARED", "Zero outstanding cash advances", "Roberto Ong (SIGNED)", "2026-09-03"],
        ["Human Resources (HR)", "CLEARED", "Exit interview completed, exit survey filed", "Grace Diaz (SIGNED)", "2026-09-04"],
    ]

    t = Table(table_data, colWidths=[120, 90, 170, 120, 60])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B4C7E")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    doc.build(story)


def main():
    samples_dir = Path(__file__).resolve().parent.parent / "samples"
    samples_dir.mkdir(exist_ok=True)

    generate_quit_claim(str(samples_dir / "quit_claim_valid.pdf"), is_valid=True)
    generate_quit_claim(str(samples_dir / "quit_claim_mismatch.pdf"), is_valid=False)

    generate_bank_proof_image(str(samples_dir / "bank_gcash_valid.png"), is_valid=True)
    generate_bank_proof_image(str(samples_dir / "bank_bad_format.png"), is_valid=False)

    generate_clearance_sheet(str(samples_dir / "clearance_sheet_valid.pdf"), is_valid=True)
    generate_clearance_sheet(str(samples_dir / "clearance_missing_it.pdf"), is_valid=False)

    print("Successfully generated 6 sample fixtures in:", samples_dir)


if __name__ == "__main__":
    main()
