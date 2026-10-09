"""
Script to generate Mirai_SoT_Policy_Handbook_2026.pdf
MirAI School of Technology (SoT) Official Student Policy Handbook 2026
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os

def generate_handbook(output_path="Mirai_SoT_Policy_Handbook_2026.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=12,
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=20,
        alignment=1
    )
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#2B6CB0'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#2D3748'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("MirAI School of Technology (SoT)", title_style))
    story.append(Paragraph("Official Student Policy & Academic Regulations Handbook (Academic Year 2026)", subtitle_style))
    story.append(Spacer(1, 10))

    # Section 1: Academic Regulations & Attendance Framework
    story.append(Paragraph("1. Academic Regulations & Attendance Framework", h1_style))
    story.append(Paragraph(
        "Regular class attendance is mandatory across all undergraduate and postgraduate engineering courses. "
        "Students are expected to maintain minimum prescribed attendance levels in every registered subject to qualify "
        "for continuous internal assessment marks and end-semester examinations.",
        body_style
    ))
    story.append(Paragraph("1.1 Attendance Marking & Continuous Assessment Weightage", h2_style))
    story.append(Paragraph(
        "Internal assessment marks for regular attendance are allocated strictly based on the overall attendance percentage "
        "recorded in the university's biometric and digital portal at the close of the instructional semester as follows:",
        body_style
    ))

    # Attendance Table
    table_data = [
        ["Attendance Bracket (%)", "Continuous Assessment Marks (Out of 10)", "Eligibility / Status"],
        ["90% and above", "10 Marks", "Full Honors Eligibility"],
        ["85% to 89.9%", "8 Marks", "Standard Regular"],
        ["80% to 84.9%", "6 Marks", "Standard Regular"],
        ["70% to 79.9%", "4 Marks", "Conditional Regular (Minimum Standard)"],
        ["65% to 69.9%", "2 Marks", "Warning Issued / Condonation Applicable"],
        ["Below 65%", "0 Marks", "Debarred from Semester End Examinations"]
    ]
    t = Table(table_data, colWidths=[160, 200, 160])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ALIGN', (1,0), (1,-1), 'CENTER')
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Specific clarification on attendance scoring: A student securing exactly 72% attendance falls under the 70% to 79.9% bracket "
        "and is awarded exactly 4 attendance marks.",
        body_style
    ))

    # Section 2: Medical Leave, Absenteeism, and Campus Administration
    story.append(Paragraph("2. Leave of Absence & Medical Leave Protocols", h1_style))
    story.append(Paragraph(
        "Students absenting themselves due to verified medical illness or hospitalization must strictly adhere to the designated "
        "campus administrative channels to obtain attendance condonation.",
        body_style
    ))
    story.append(Paragraph("2.1 Campus-Specific Medical Reporting Officers", h2_style))
    story.append(Paragraph("• <b>Main City Campus:</b> Applications and hospital discharge certificates must be emailed to Prof. K. Ramanathan (Dean of Student Welfare) at studentwelfare.main@mirai.edu.", bullet_style))
    story.append(Paragraph("• <b>Ratnam Campus:</b> Students studying at the Ratnam campus who require medical leave must directly email all medical certificates and hospital documentation to Yashaswini Ma'am (Ratnam Campus Academic Coordinator) at yashaswini.ratnam@mirai.edu.", bullet_style))
    story.append(Paragraph("• <b>North Extension Campus:</b> All medical claims must be filed directly with Dr. Arisudan Mehta.", bullet_style))

    story.append(Paragraph("2.2 Timelines for Medical Leave Submission", h2_style))
    story.append(Paragraph(
        "All medical documentation, including physician fitness certificates, diagnostic reports, and leave applications, "
        "must be submitted within exactly 7 days of the conclusion of the illness or medical treatment. "
        "Submissions beyond this strict 7-day window will be automatically rejected by the portal, and no retroactive attendance credit will be granted under any circumstance.",
        body_style
    ))

    story.append(Spacer(1, 8))

    # Section 3: Student Organizations, Tech Club & Society Creation
    story.append(Paragraph("3. Student Clubs, Societies & Extracurricular Governance", h1_style))
    story.append(Paragraph(
        "MirAI School of Technology encourages holistic professional development through registered student organizations. "
        "The overarching technical body of the university is the Tech Club.",
        body_style
    ))
    story.append(Paragraph("3.1 Formation of New Societies & Special Interest Groups (SIGs)", h2_style))
    story.append(Paragraph(
        "Any student cohort desiring to launch a new specialized society or wing (such as a Cybersecurity society, AI Research group, or Robotics guild) "
        "under the umbrella of the Tech Club must adhere to the formal statutory procedure:",
        body_style
    ))
    story.append(Paragraph("1. <b>Minimum Batch Support:</b> The founding team must demonstrate demonstrable interest by securing the endorsement of at least 40% batch support from their registered student cohort.", bullet_style))
    story.append(Paragraph("2. <b>Proposal Submission Protocol:</b> The charter, objective roadmap, and 40% batch petition must be submitted directly to the Faculty Coordinator of the Tech Club first. Under no circumstances should students approach University Management directly for initial approvals.", bullet_style))
    story.append(Paragraph("3. <b>Review & Final Charter:</b> The Faculty Coordinator will conduct a feasibility review and, upon satisfaction, forward the ratified charter to the Office of Student Affairs.", bullet_style))

    story.append(Spacer(1, 8))

    # Section 4: Campus Code of Conduct, Substance Policies & Disciplinary Action
    story.append(Paragraph("4. Campus Code of Conduct & Substance Regulations", h1_style))
    story.append(Paragraph(
        "MirAI School of Technology is a strictly declared zero-tolerance, smoke-free, and substance-free institution. "
        "All enrolled students, faculty, and visitors must uphold the highest standards of civic responsibility.",
        body_style
    ))
    story.append(Paragraph("4.1 Tobacco and Smoking Prohibition", h2_style))
    story.append(Paragraph(
        "Smoking cigarettes, consuming e-cigarettes/vapes, or possessing any tobacco products within campus grounds, hostel blocks, academic corridors, "
        "canteens, or parking zones is strictly prohibited.",
        body_style
    ))
    story.append(Paragraph("4.2 Penalties and Disciplinary Committee Proceedings", h2_style))
    story.append(Paragraph(
        "Any student apprehended smoking or in possession of tobacco products on campus will be immediately reported to the Proctorial Board and "
        "referred to the Disciplinary Committee for formal investigation and appropriate disciplinary action. Disciplinary action may include "
        "formal behavioral reprimands, suspension of hostel privileges, or mandatory community service. "
        "Note: The handbook does not prescribe or fix any specific monetary fine for smoking violations; all penalties are determined by the Disciplinary Committee based on hearing outcomes.",
        body_style
    ))

    # Section 5: Academic Integrity & Grievance Redressal
    story.append(Paragraph("5. Academic Integrity and Grievance Redressal", h1_style))
    story.append(Paragraph(
        "Plagiarism, unauthorized collaboration in graded assignments, and unauthorized use of automated tools without faculty disclosure "
        "constitute major academic misconduct. Grievances regarding evaluation must be filed with the Departmental Ombudsperson within 5 working days of grade publication.",
        body_style
    ))

    doc.build(story)
    print(f"Handbook PDF generated successfully at: {output_path}")

if __name__ == "__main__":
    generate_handbook("/Users/debarghyamisra09/GenAI/policyrag/Mirai_SoT_Policy_Handbook_2026.pdf")
    generate_handbook("/Users/debarghyamisra09/GenAI/Mirai_SoT_Policy_Handbook_2026.pdf")
