"""
services/report_service.py — Modern Executive PDF & CSV Report Generator
ResumeMatch.ai

Generates beautifully formatted, executive-ready PDF reports and CSV exports.
Handles fallback font sanitization (Latin-1/UTF-8) and ensures clean presentation.
"""

import os
import csv
from datetime import datetime

def clean_pdf_text(text):
    """Sanitize text strings for PDF engine rendering."""
    if text is None:
        return ''
    text = str(text)
    replacements = {
        '•': '-', '—': '-', '–': '-', '“': '"', '”': '"',
        '’': "'", '‘': "'", '…': '...', '™': '', '®': '',
        '©': '', '\xa0': ' '
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode('latin-1', 'replace').decode('latin-1')


def generate_candidate_pdf(candidate, score, jd, output_path):
    """
    Generate an executive-grade structured PDF report for a single candidate.
    Uses ReportLab / FPDF with automatic fallback to guarantee valid file generation.
    """
    try:
        try:
            from fpdf import FPDF
        except ImportError:
            from fpdf2 import FPDF

        class CandidatePDF(FPDF):
            def header(self):
                # Dark Header Banner
                self.set_fill_color(15, 23, 42)
                self.rect(0, 0, 210, 36, 'F')
                self.set_text_color(255, 255, 255)
                self.set_font('Helvetica', 'B', 18)
                self.set_xy(15, 8)
                self.cell(0, 8, 'ResuMatch.Ai', new_x='LMARGIN', new_y='NEXT')
                self.set_font('Helvetica', '', 9.5)
                self.set_text_color(165, 180, 252)
                self.set_x(15)
                self.cell(0, 5, 'Hire Smart with ResuMatch.Ai -- Executive Candidate Evaluation Report', new_x='LMARGIN', new_y='NEXT')

            def footer(self):
                self.set_y(-15)
                self.set_font('Helvetica', 'I', 8)
                self.set_text_color(148, 163, 184)
                self.cell(0, 6, 'ResuMatch.Ai -- Confidential Candidate Evaluation Matrix', align='C')

        pdf = CandidatePDF(unit='mm', format='A4')
        pdf.set_margins(15, 15, 15)
        pdf.add_page()

        # Candidate Details Card
        pdf.set_xy(15, 42)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(15, 42, 180, 44, 'DF')

        pdf.set_xy(20, 46)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font('Helvetica', 'B', 15)
        pdf.cell(0, 7, clean_pdf_text(candidate.get('name', 'Unknown Candidate')), new_x='LMARGIN', new_y='NEXT')

        info_left = [
            ('Email:', clean_pdf_text(candidate.get('email') or candidate.get('parsed_data', {}).get('email') or 'N/A')),
            ('Phone:', clean_pdf_text(candidate.get('phone') or candidate.get('parsed_data', {}).get('phone') or 'N/A')),
            ('File:', clean_pdf_text(candidate.get('resume_filename') or 'Uploaded Resume')),
        ]
        info_right = [
            ('Target Role:', clean_pdf_text(jd.get('title') or candidate.get('job_title') or 'Software Professional')),
            ('Company:', clean_pdf_text(jd.get('company') or 'Acme Corp')),
            ('Report Date:', datetime.now().strftime('%B %d, %Y')),
        ]

        y_pos = 56
        for label, val in info_left:
            pdf.set_xy(20, y_pos)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(24, 5, label)
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(60, 5, val[:35])
            y_pos += 5.5

        y_pos = 56
        for label, val in info_right:
            pdf.set_xy(108, y_pos)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(26, 5, label)
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(60, 5, val[:35])
            y_pos += 5.5

        # Overall ATS Score Banner
        overall = float(score.get('overall_score', 0))
        status_text = clean_pdf_text(score.get('status') or candidate.get('status') or 'Pending').upper()

        if overall >= 70:
            fill_r, fill_g, fill_b = 240, 253, 244
            draw_r, draw_g, draw_b = 187, 247, 208
            text_r, text_g, text_b = 22, 101, 52
        elif overall >= 40:
            fill_r, fill_g, fill_b = 254, 252, 232
            draw_r, draw_g, draw_b = 254, 240, 138
            text_r, text_g, text_b = 133, 77, 14
        else:
            fill_r, fill_g, fill_b = 254, 242, 242
            draw_r, draw_g, draw_b = 254, 202, 202
            text_r, text_g, text_b = 153, 27, 27

        pdf.set_xy(15, 92)
        pdf.set_fill_color(fill_r, fill_g, fill_b)
        pdf.set_draw_color(draw_r, draw_g, draw_b)
        pdf.rect(15, 92, 180, 22, 'DF')

        pdf.set_xy(22, 95)
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_text_color(text_r, text_g, text_b)
        pdf.cell(45, 16, f"{overall:.1f}%")

        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(65, 16, "OVERALL ATS MATCH SCORE")

        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(60, 16, f"STATUS: {status_text}", align='R', new_x='LMARGIN', new_y='NEXT')

        # Detailed Breakdown Table
        pdf.set_xy(15, 120)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, "DETAILED SCORE BREAKDOWN", new_x='LMARGIN', new_y='NEXT')

        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_draw_color(203, 213, 225)
        pdf.cell(60, 7, " Evaluation Category", 1, 0, 'L', True)
        pdf.cell(35, 7, "Score", 1, 0, 'C', True)
        pdf.cell(85, 7, "Visual Indicator Bar", 1, 1, 'L', True)

        breakdown = [
            ("Skill Match", float(score.get('skill_score', 0))),
            ("Keyword Alignment", float(score.get('keyword_score', 0))),
            ("Experience Match", float(score.get('experience_score', 0))),
            ("Education Match", float(score.get('education_score', 0)))
        ]

        pdf.set_font('Helvetica', '', 9)
        for cat_name, cat_val in breakdown:
            pdf.set_x(15)
            pdf.cell(60, 6.5, f" {cat_name}", 1, 0, 'L')
            pdf.cell(35, 6.5, f"{cat_val:.1f}%", 1, 0, 'C')

            cur_x = pdf.get_x()
            cur_y = pdf.get_y()
            pdf.cell(85, 6.5, "", 1, 1, 'L')

            bar_w = max(1.0, (cat_val / 100.0) * 77.0)
            if cat_val >= 70:
                pdf.set_fill_color(16, 185, 129)
            elif cat_val >= 40:
                pdf.set_fill_color(245, 158, 11)
            else:
                pdf.set_fill_color(239, 68, 68)

            pdf.rect(cur_x + 4, cur_y + 1.8, bar_w, 3, 'F')

        # Executive Summary Box
        pdf.ln(5)
        pdf.set_x(15)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, "EXECUTIVE MATCH SUMMARY", new_x='LMARGIN', new_y='NEXT')

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 65, 85)
        pdf.set_fill_color(248, 250, 252)

        summary_text = clean_pdf_text(score.get('summary') or candidate.get('parsed_data', {}).get('summary') or 'Candidate evaluation completed based on resume profile and job requirements.')
        pdf.multi_cell(180, 5, summary_text, border=1, fill=True)

        # Matched & Missing Skills
        pdf.ln(4)
        curr_y = pdf.get_y()
        pdf.set_xy(15, curr_y)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(22, 101, 52)
        pdf.cell(88, 6, "MATCHED SKILLS")

        pdf.set_xy(107, curr_y)
        pdf.set_text_color(153, 27, 27)
        pdf.cell(88, 6, "MISSING SKILLS", new_x='LMARGIN', new_y='NEXT')

        matched = score.get('matched_skills', [])
        missing = score.get('missing_skills', [])

        if isinstance(matched, str):
            try:
                import json
                matched = json.loads(matched)
            except Exception:
                matched = [matched]

        if isinstance(missing, str):
            try:
                import json
                missing = json.loads(missing)
            except Exception:
                missing = [missing]

        matched_list = [clean_pdf_text(s) for s in matched if str(s).strip()]
        missing_list = [clean_pdf_text(s) for s in missing if str(s).strip()]

        if not matched_list:
            cand_skills = candidate.get('parsed_data', {}).get('skills', [])
            if isinstance(cand_skills, list):
                matched_list = [clean_pdf_text(s) for s in cand_skills]

        matched_str = ", ".join(matched_list) if matched_list else "General technical skills identified"
        missing_str = ", ".join(missing_list) if missing_list else "None identified"

        grid_y = pdf.get_y()
        pdf.set_font('Helvetica', '', 8.5)
        pdf.set_text_color(51, 65, 85)

        pdf.set_xy(15, grid_y)
        pdf.multi_cell(88, 4.5, matched_str, border=1)
        h_left = pdf.get_y() - grid_y

        pdf.set_xy(107, grid_y)
        pdf.multi_cell(88, 4.5, missing_str, border=1)
        h_right = pdf.get_y() - grid_y

        next_y = grid_y + max(h_left, h_right) + 4

        # Recommendations
        if next_y < 255:
            pdf.set_xy(15, next_y)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 6, "RECRUITER RECOMMENDATIONS", new_x='LMARGIN', new_y='NEXT')

            pdf.set_font('Helvetica', '', 8.5)
            pdf.set_text_color(71, 85, 105)
            suggs = score.get('suggestions', [])
            if isinstance(suggs, str):
                try:
                    import json
                    suggs = json.loads(suggs)
                except Exception:
                    suggs = [suggs]

            if suggs and isinstance(suggs, list):
                for sg in suggs[:3]:
                    pdf.set_x(15)
                    pdf.multi_cell(180, 4.5, f"- {clean_pdf_text(sg)}")
            else:
                pdf.set_x(15)
                pdf.cell(0, 4.5, "- Profile meets requirements. Recommended for technical screening interview.", new_x='LMARGIN', new_y='NEXT')

        pdf.output(output_path)
        return output_path

    except Exception as err:
        print(f"FPDF generation error, attempting ReportLab fallback: {err}")
        return _generate_candidate_pdf_reportlab(candidate, score, jd, output_path)


def _generate_candidate_pdf_reportlab(candidate, score, jd, output_path):
    """Fallback candidate PDF generation using ReportLab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=12
        )
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )

        elements.append(Paragraph("ResuMatch.Ai -- Executive Candidate Report", title_style))
        elements.append(Paragraph(f"Candidate: <b>{candidate.get('name', 'Unknown')}</b> | Role: {jd.get('title', 'Target Role')}", subtitle_style))
        elements.append(Spacer(1, 10))

        overall = float(score.get('overall_score', 0))
        score_data = [
            ['Overall Match Score', f"{overall:.1f}%"],
            ['Skill Match', f"{float(score.get('skill_score', 0)):.1f}%"],
            ['Experience Match', f"{float(score.get('experience_score', 0)):.1f}%"],
            ['Education Match', f"{float(score.get('education_score', 0)):.1f}%"],
            ['Keyword Alignment', f"{float(score.get('keyword_score', 0)):.1f}%"]
        ]
        score_table = Table(score_data, colWidths=[200, 200])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#0f172a')),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 14))

        summary_txt = score.get('summary') or candidate.get('parsed_data', {}).get('summary') or 'Candidate evaluation completed.'
        elements.append(Paragraph("<b>Executive Summary:</b>", body_style))
        elements.append(Paragraph(summary_txt, body_style))
        elements.append(Spacer(1, 14))

        matched = score.get('matched_skills', [])
        missing = score.get('missing_skills', [])

        if isinstance(matched, list):
            matched_clean = ", ".join([clean_pdf_text(s) for s in matched]) if matched else 'General technical skills'
        else:
            matched_clean = clean_pdf_text(matched) or 'General technical skills'

        if isinstance(missing, list):
            missing_clean = ", ".join([clean_pdf_text(s) for s in missing]) if missing else 'None'
        else:
            missing_clean = clean_pdf_text(missing) or 'None'

        skills_data = [
            ['Matched Skills', 'Missing Skills'],
            [Paragraph(matched_clean, body_style), Paragraph(missing_clean, body_style)]
        ]
        skills_table = Table(skills_data, colWidths=[250, 250])
        skills_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), colors.HexColor('#dcfce7')),
            ('BACKGROUND', (1,0), (1,0), colors.HexColor('#fee2e2')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(skills_table)

        doc.build(elements)
        return output_path
    except Exception as e:
        print(f"ReportLab fallback failed: {e}")
        return False


def generate_candidates_csv(candidates_data, output_path):
    """
    Export candidate records and evaluation matrix cleanly to a CSV file.
    Includes UTF-8 BOM so Excel opens it with perfect formatting and zero errors.
    """
    try:
        fieldnames = [
            'Candidate ID',
            'Candidate Name',
            'Email Address',
            'Phone Number',
            'Target Job Title',
            'Status',
            'Overall ATS Match (%)',
            'Skill Match (%)',
            'Experience Match (%)',
            'Education Match (%)',
            'Keyword Match (%)',
            'Matched Skills',
            'Missing Skills',
            'Summary',
            'Uploaded Date'
        ]

        # Use utf-8-sig (UTF-8 with BOM) so Microsoft Excel opens it cleanly
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in candidates_data:
                # Handle candidate data format variations
                cand_id = item.get('candidate_id') or item.get('id') or ''
                name    = item.get('name') or 'Candidate'
                email   = item.get('email') or ''
                phone   = item.get('phone') or ''
                job     = item.get('jd_title') or item.get('job_title') or 'Software Professional'
                status  = (item.get('status') or 'Pending').capitalize()

                overall = float(item.get('overall_score') or item.get('match_score') or item.get('quality_score') or 0)
                skill   = float(item.get('skill_score') or overall)
                exp     = float(item.get('experience_score') or overall)
                edu     = float(item.get('education_score') or overall)
                kw      = float(item.get('keyword_score') or overall)

                matched = item.get('matched_skills') or []
                missing = item.get('missing_skills') or []

                if isinstance(matched, list):
                    matched_str = "; ".join([str(s) for s in matched])
                else:
                    matched_str = str(matched)

                if isinstance(missing, list):
                    missing_str = "; ".join([str(s) for s in missing])
                else:
                    missing_str = str(missing)

                summary = item.get('summary') or ''
                if not summary and isinstance(item.get('parsed_data'), dict):
                    summary = item['parsed_data'].get('summary', '')

                date_str = item.get('uploaded_at') or item.get('created_at') or datetime.now().strftime('%Y-%m-%d')

                writer.writerow({
                    'Candidate ID': cand_id,
                    'Candidate Name': name,
                    'Email Address': email,
                    'Phone Number': phone,
                    'Target Job Title': job,
                    'Status': status,
                    'Overall ATS Match (%)': f"{overall:.1f}",
                    'Skill Match (%)': f"{skill:.1f}",
                    'Experience Match (%)': f"{exp:.1f}",
                    'Education Match (%)': f"{edu:.1f}",
                    'Keyword Match (%)': f"{kw:.1f}",
                    'Matched Skills': matched_str,
                    'Missing Skills': missing_str,
                    'Summary': summary.replace('\n', ' '),
                    'Uploaded Date': date_str
                })
        return output_path
    except Exception as e:
        print(f"Error generating candidates CSV: {e}")
        return False

# Alias function name
generate_csv = generate_candidates_csv


def generate_ranking_pdf(scores, jd, output_path):
    """
    Generate a full candidate ranking summary PDF report.
    """
    try:
        try:
            from fpdf import FPDF
        except ImportError:
            from fpdf2 import FPDF

        class RankingPDF(FPDF):
            def header(self):
                self.set_fill_color(15, 23, 42)
                self.rect(0, 0, 210, 36, 'F')
                self.set_text_color(255, 255, 255)
                self.set_font('Helvetica', 'B', 18)
                self.set_xy(15, 8)
                self.cell(0, 8, 'ResuMatch.Ai -- Candidate Rankings', new_x='LMARGIN', new_y='NEXT')
                self.set_font('Helvetica', '', 10)
                self.set_text_color(165, 180, 252)
                self.set_x(15)
                title_jd = clean_pdf_text(jd.get('title', 'Job Position'))
                self.cell(0, 5, f"Role: {title_jd} -- Ranked ATS Candidate Summary", new_x='LMARGIN', new_y='NEXT')

            def footer(self):
                self.set_y(-15)
                self.set_font('Helvetica', 'I', 8)
                self.set_text_color(148, 163, 184)
                self.cell(0, 6, f"ResuMatch.Ai Candidate Rankings -- Page {self.page_no()}", align='C')

        pdf = RankingPDF(unit='mm', format='A4')
        pdf.set_margins(15, 15, 15)
        pdf.add_page()

        pdf.set_xy(15, 44)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_draw_color(203, 213, 225)
        pdf.set_text_color(15, 23, 42)

        pdf.cell(12, 7, "Rank", 1, 0, 'C', True)
        pdf.cell(55, 7, " Candidate Name", 1, 0, 'L', True)
        pdf.cell(30, 7, "Overall Score", 1, 0, 'C', True)
        pdf.cell(30, 7, "Skill Match", 1, 0, 'C', True)
        pdf.cell(30, 7, "Status", 1, 0, 'C', True)
        pdf.cell(23, 7, "Date Scored", 1, 1, 'C', True)

        pdf.set_font('Helvetica', '', 9)
        for idx, s in enumerate(scores, 1):
            pdf.set_x(15)
            pdf.cell(12, 6.5, str(idx), 1, 0, 'C')
            pdf.cell(55, 6.5, f" {clean_pdf_text(s.get('name', 'Candidate'))[:28]}", 1, 0, 'L')
            score_val = float(s.get('overall_score', 0))
            pdf.cell(30, 6.5, f"{score_val:.1f}%", 1, 0, 'C')
            pdf.cell(30, 6.5, f"{int(s.get('skill_score', score_val))}%", 1, 0, 'C')
            pdf.cell(30, 6.5, clean_pdf_text(s.get('status', 'Pending')).capitalize(), 1, 0, 'C')
            pdf.cell(23, 6.5, datetime.now().strftime('%m/%d/%Y'), 1, 1, 'C')

        pdf.output(output_path)
        return output_path
    except Exception as e:
        print(f"Error generating ranking PDF: {e}")
        return False