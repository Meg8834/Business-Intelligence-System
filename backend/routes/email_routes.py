from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.db_config import get_db
from database.models import User, BusinessData
from models.anomaly_model import detect_anomalies
from utils.auth_utils import get_current_user
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter()


class EmailRequest(BaseModel):
    to_email: str


def build_email_html(anomalies: list, total: int, user_name: str) -> str:
    rows_html = ""
    for a in anomalies:
        rows_html += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #eee;">{a['month']}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #eee;">Rs. {float(a['revenue']):,.2f}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #eee;">Rs. {float(a['expenses']):,.2f}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #eee;color:#e63946;font-weight:bold;">Anomaly</td>
        </tr>"""

    return f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
    <div style="max-width:600px;margin:auto;background:#fff;border-radius:8px;overflow:hidden;">
        <div style="background:#e63946;padding:24px 32px;">
            <h2 style="color:#fff;margin:0;">Anomaly Alert — {user_name}</h2>
            <p style="color:#ffc;margin:8px 0 0;">Business Decision Intelligence System</p>
        </div>
        <div style="padding:24px 32px;">
            <p style="font-size:15px;color:#333;">
                Hi <strong>{user_name}</strong>, 
                <strong>{len(anomalies)} anomalous month(s)</strong> detected in your data 
                ({total} total records).
            </p>
            <table style="width:100%;border-collapse:collapse;margin-top:16px;">
                <thead>
                    <tr style="background:#f8f9ff;">
                        <th style="padding:10px 12px;text-align:left;color:#4361ee;">Month</th>
                        <th style="padding:10px 12px;text-align:left;color:#4361ee;">Revenue</th>
                        <th style="padding:10px 12px;text-align:left;color:#4361ee;">Expenses</th>
                        <th style="padding:10px 12px;text-align:left;color:#4361ee;">Status</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        <div style="background:#f8f9ff;padding:12px 32px;text-align:center;">
            <p style="font-size:11px;color:#aaa;margin:0;">Business Decision Intelligence System</p>
        </div>
    </div>
    </body></html>"""


@router.post("/email/alert")
def send_anomaly_alert(
    request: EmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sends anomaly alert email for the logged-in user's data only."""
    rows = db.query(BusinessData).filter(
        BusinessData.user_id == current_user.id
    ).order_by(BusinessData.id.asc()).all()

    if not rows:
        raise HTTPException(status_code=400, detail="No data found. Upload CSV first.")

    data = [r.to_dict() for r in rows]
    tagged = detect_anomalies(data)
    anomalies = [r for r in tagged if r["is_anomaly"]]

    if not anomalies:
        return {"message": "No anomalies detected. No alert sent.", "anomaly_count": 0}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Anomaly Alert — {len(anomalies)} unusual month(s) in your business data"
    msg["From"] = EMAIL_USER
    msg["To"] = request.to_email
    msg.attach(MIMEText(build_email_html(anomalies, len(rows), current_user.name), "html"))

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, request.to_email, msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email failed: {str(e)}")

    return {
        "message": f"Alert sent to {request.to_email}",
        "anomaly_count": len(anomalies),
        "anomalous_months": [a["month"] for a in anomalies],
    }