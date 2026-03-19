from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database.db_config import get_db
from database.models import User, BusinessData
from models.health_score import calculate_health_score
from models.anomaly_model import detect_anomalies
from models.forecasting_model import forecast_revenue
from models.explanation_engine import generate_explanation
from utils.auth_utils import get_current_user
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from datetime import datetime

router = APIRouter()


@router.get("/report/download")
def download_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates PDF report using only the logged-in user's data."""
    rows = db.query(BusinessData).filter(
        BusinessData.user_id == current_user.id
    ).order_by(BusinessData.id.asc()).all()

    if not rows:
        raise HTTPException(status_code=400, detail="No data found. Upload CSV first.")

    latest = rows[-1]
    health = calculate_health_score(
        latest.revenue, latest.expenses,
        latest.marketing_spend, latest.customer_growth
    )
    data = [r.to_dict() for r in rows]
    tagged = detect_anomalies(data)
    anomaly_count = sum(1 for r in tagged if r["is_anomaly"])
    revenues = [r.revenue for r in rows]
    forecast = forecast_revenue(revenues, periods=3) if len(revenues) >= 2 else []
    explanation = generate_explanation(
        latest.revenue, latest.expenses,
        latest.marketing_spend, latest.customer_growth,
        health["health_score"], health["label"],
        anomaly_count, forecast[0] if forecast else None
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=20,
                                  textColor=colors.HexColor('#1a1a2e'), spaceAfter=6, alignment=TA_CENTER)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=13,
                                    textColor=colors.HexColor('#16213e'), spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10,
                                 textColor=colors.HexColor('#333333'), spaceAfter=4, leading=16)

    story.append(Paragraph(f"Business Intelligence Report — {current_user.name}", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}  |  "
        f"Latest Month: {latest.month}  |  Records: {len(rows)}",
        ParagraphStyle('sub', parent=styles['Normal'], fontSize=9,
                       textColor=colors.HexColor('#888888'), alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=colors.HexColor('#4361ee'), spaceAfter=12))

    # Health Score
    story.append(Paragraph("Business Health Score", heading_style))
    score = health["health_score"]
    score_color = '#2dc653' if score >= 80 else '#f4a261' if score >= 60 else '#e63946'
    score_table = Table(
        [["Score", "Rating", "Profit Margin", "Expense Ratio"],
         [f"{score}/100", health["label"],
          f"{health['breakdown']['profit_margin_pct']}%",
          f"{health['breakdown']['expense_ratio_pct']}%"]],
        colWidths=[4*cm, 4*cm, 4*cm, 4*cm]
    )
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4361ee')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f0f4ff')),
        ('TEXTCOLOR', (0,1), (0,1), colors.HexColor(score_color)),
        ('FONTNAME', (0,1), (0,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 12),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.3*cm))

    # Metrics
    story.append(Paragraph("Latest Business Metrics", heading_style))
    profit = latest.revenue - latest.expenses
    metrics_table = Table(
        [["Metric", "Value"],
         ["Revenue", f"Rs. {latest.revenue:,.2f}"],
         ["Expenses", f"Rs. {latest.expenses:,.2f}"],
         ["Profit", f"Rs. {profit:,.2f}"],
         ["Marketing Spend", f"Rs. {latest.marketing_spend:,.2f}"],
         ["Customer Growth", f"{latest.customer_growth}%"]],
        colWidths=[8*cm, 8*cm]
    )
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4361ee')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9ff')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.3*cm))

    # Forecast
    if forecast:
        story.append(Paragraph("Revenue Forecast (Next 3 Months)", heading_style))
        forecast_table = Table(
            [["Month", "Predicted Revenue"]] +
            [[f"Forecast Month {i+1}", f"Rs. {v:,.2f}"] for i, v in enumerate(forecast)],
            colWidths=[8*cm, 8*cm]
        )
        forecast_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4361ee')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9ff')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(forecast_table)
        story.append(Spacer(1, 0.3*cm))

    # Anomaly
    story.append(Paragraph("Anomaly Detection", heading_style))
    anomaly_months = [r["month"] for r in tagged if r["is_anomaly"]]
    story.append(Paragraph(
        f"Anomalies in {len(anomaly_months)} month(s): {', '.join(anomaly_months)}. Investigate these months." if anomaly_months
        else "No anomalies detected. Data is consistent.",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))

    # AI Insights
    story.append(Paragraph("AI-Generated Insights", heading_style))
    story.append(Paragraph(explanation["summary"], body_style))
    for insight in explanation["insights"]:
        story.append(Paragraph(f"- {insight}", body_style))
    story.append(Spacer(1, 0.4*cm))

    # Historical table
    story.append(Paragraph("Historical Data", heading_style))
    table_data = [["Month", "Revenue", "Expenses", "Marketing", "Growth", "Anomaly"]]
    for r in rows:
        is_anom = next((t["is_anomaly"] for t in tagged if t["id"] == r.id), False)
        table_data.append([
            r.month, f"Rs.{r.revenue:,.0f}", f"Rs.{r.expenses:,.0f}",
            f"Rs.{r.marketing_spend:,.0f}", f"{r.customer_growth}%",
            "YES" if is_anom else "No"
        ])
    hist_table = Table(table_data, colWidths=[3*cm, 3.2*cm, 3.2*cm, 3*cm, 2.8*cm, 1.8*cm])
    style_cmds = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4361ee')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9ff')]),
    ]
    for i, r in enumerate(rows):
        is_anom = next((t["is_anomaly"] for t in tagged if t["id"] == r.id), False)
        if is_anom:
            style_cmds += [
                ('BACKGROUND', (0, i+1), (-1, i+1), colors.HexColor('#fff0f0')),
                ('TEXTCOLOR', (5, i+1), (5, i+1), colors.HexColor('#e63946')),
            ]
    hist_table.setStyle(TableStyle(style_cmds))
    story.append(hist_table)

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=6))
    story.append(Paragraph(
        "Business Decision Intelligence System | Powered by ML and FastAPI",
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#aaaaaa'), alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    filename = f"report_{current_user.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})