import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.core.database import supabase
from app.core.security import get_current_user
from app.agents.followup_writer import write_followup, FollowupWriterOutput
from app.api.v1.brief import run_agent_with_backoff, log_agent_error
from app.core.limiter import limiter

router = APIRouter(prefix="/invoices", tags=["invoices"])

def render_invoice_html(invoice: dict, user_profile: dict) -> str:
    """
    Renders a premium, light-themed HTML layout matching our design system 
    for A4 print compilation.
    """
    amount = float(invoice.get("amount_inr") or 0)
    gst = float(invoice.get("gst_amount") or 0)
    total = float(invoice.get("total_inr") or 0)
    name = user_profile.get("name") or "Freelancer"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 20mm;
            }}
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #2D3748;
                font-size: 14px;
                line-height: 1.5;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                border-bottom: 2px solid #E2E8F0;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                color: #4A5568;
                letter-spacing: -0.5px;
            }}
            .logo span {{
                color: #3182CE;
            }}
            .invoice-title {{
                text-align: right;
            }}
            .invoice-title h1 {{
                margin: 0;
                font-size: 28px;
                color: #2D3748;
                font-weight: 300;
            }}
            .invoice-details {{
                margin-top: 5px;
                font-size: 12px;
                color: #718096;
            }}
            .addresses {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 40px;
            }}
            .address-box {{
                width: 45%;
            }}
            .address-box h3 {{
                margin: 0 0 10px 0;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #A0AEC0;
            }}
            .address-box p {{
                margin: 2px 0;
            }}
            .table-container {{
                margin-bottom: 40px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th {{
                background-color: #F7FAFC;
                color: #4A5568;
                font-weight: 600;
                text-align: left;
                padding: 12px;
                font-size: 12px;
                text-transform: uppercase;
                border-bottom: 2px solid #E2E8F0;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #E2E8F0;
            }}
            .amount-col {{
                text-align: right;
            }}
            .totals {{
                display: flex;
                justify-content: flex-end;
                margin-bottom: 40px;
            }}
            .totals-table {{
                width: 300px;
            }}
            .totals-table td {{
                padding: 8px 12px;
                border: none;
            }}
            .totals-table tr.grand-total {{
                border-top: 2px solid #E2E8F0;
                font-size: 16px;
                font-weight: bold;
            }}
            .payment-instructions {{
                background-color: #EBF8FF;
                border-left: 4px solid #3182CE;
                padding: 15px;
                border-radius: 4px;
                margin-top: 40px;
            }}
            .payment-instructions h4 {{
                margin: 0 0 8px 0;
                color: #2B6CB0;
            }}
            .payment-instructions p {{
                margin: 2px 0;
                font-size: 13px;
            }}
            .footer {{
                text-align: center;
                margin-top: 60px;
                font-size: 11px;
                color: #A0AEC0;
                border-top: 1px solid #E2E8F0;
                padding-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">Gig<span>.ai</span></div>
            <div class="invoice-title">
                <h1>INVOICE</h1>
                <div class="invoice-details">
                    <p><strong>Invoice No:</strong> {invoice.get("invoice_number")}</p>
                    <p><strong>Date of Issue:</strong> {invoice.get("created_at")[:10] if invoice.get("created_at") else ""}</p>
                    <p><strong>Due Date:</strong> {invoice.get("due_date")}</p>
                </div>
            </div>
        </div>

        <div class="addresses">
            <div class="address-box">
                <h3>From:</h3>
                <p><strong>{name}</strong></p>
                <p>{user_profile.get("email")}</p>
            </div>
            <div class="address-box">
                <h3>To:</h3>
                <p><strong>{invoice.get("client_name")}</strong></p>
                <p>{invoice.get("client_email")}</p>
            </div>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th class="amount-col">Amount (INR)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <strong>{invoice.get("milestone_title")}</strong><br>
                            <span style="font-size: 12px; color: #718096;">Project: {invoice.get("project_title")}</span>
                        </td>
                        <td class="amount-col">{amount:,.2f}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="totals">
            <table class="totals-table">
                <tr>
                    <td>Subtotal:</td>
                    <td class="amount-col">{amount:,.2f} INR</td>
                </tr>
                <tr>
                    <td>GST (18%):</td>
                    <td class="amount-col">{gst:,.2f} INR</td>
                </tr>
                <tr class="grand-total">
                    <td>Total Due:</td>
                    <td class="amount-col">{total:,.2f} INR</td>
                </tr>
            </table>
        </div>

        <div class="payment-instructions">
            <h4>Payment Instructions</h4>
            <p><strong>UPI ID:</strong> {user_profile.get("upi_id") or "Not provided"}</p>
            {f"<p><strong>Bank Details:</strong> {user_profile.get('bank_details')}</p>" if user_profile.get("bank_details") else ""}
            <p style="margin-top: 10px; font-size: 11px; color: #4A5568;">Please transfer the total amount due by the due date. Thank you for your business!</p>
        </div>

        <div class="footer">
            <p>Generated by Gig.ai — The AI Freelance Command Centre</p>
        </div>
    </body>
    </html>
    """
    return html

@router.get("/")
def list_invoices(current_user: dict = Depends(get_current_user)):
    """
    Lists all invoices belonging to the authenticated user.
    """
    user_id = current_user["id"]
    try:
        res = supabase.table("invoices")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return res.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetches details for a single invoice. Verifies user ownership.
    """
    user_id = current_user["id"]
    try:
        res = supabase.table("invoices")\
            .select("*")\
            .eq("id", invoice_id)\
            .eq("user_id", user_id)\
            .execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        return res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

@router.patch("/{invoice_id}/paid")
def mark_invoice_as_paid(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Marks an invoice as paid. Sets the paid_at timestamp to now.
    Verifies user ownership.
    """
    user_id = current_user["id"]
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    try:
        # Check ownership first
        check = supabase.table("invoices").select("id").eq("id", invoice_id).eq("user_id", user_id).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
            
        res = supabase.table("invoices").update({
            "payment_status": "paid",
            "paid_at": now_iso
        }).eq("id", invoice_id).eq("user_id", user_id).execute()
        
        return res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update invoice: {str(e)}"
        )

@router.get("/{invoice_id}/pdf")
@limiter.limit("60/minute")
def get_invoice_pdf(
    request: Request,
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Generates a PDF layout using WeasyPrint (or falls back to mock buffer locally),
    uploads the output to Supabase Storage and returns a 1-hour signed URL.
    """
    user_id = current_user["id"]
    
    try:
        res = supabase.table("invoices").select("*").eq("id", invoice_id).eq("user_id", user_id).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        invoice = res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

    # Ensure bucket exists
    try:
        supabase.storage.create_bucket("invoices", {"public": False})
    except Exception:
        pass

    # Check cache first
    try:
        signed_url_res = supabase.storage.from_("invoices").create_signed_url(f"{invoice_id}.pdf", 3600)
        if signed_url_res and isinstance(signed_url_res, dict) and "signedURL" in signed_url_res:
            return {"pdf_url": signed_url_res["signedURL"], "cached": True}
    except Exception:
        pass

    # Cache miss: Fetch user profile to render invoice HTML
    try:
        user_res = supabase.table("users").select("*").eq("id", user_id).execute()
        user_profile = user_res.data[0] if user_res.data else {}
    except Exception:
        user_profile = {}

    html_content = render_invoice_html(invoice, user_profile)

    # Compile PDF
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
    except Exception as weasy_err:
        print(f"WeasyPrint failed locally: {str(weasy_err)}. Using mock PDF fallback.")
        pdf_bytes = f"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 50 >>\nstream\nBT /F1 12 Tf 50 700 Td ({invoice.get('invoice_number')} PDF Fallback) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000062 00000 n\n0000000121 00000 n\n0000000216 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n315\n%%EOF\n".encode("utf-8")

    # Upload PDF file to Supabase Storage bucket 'invoices'
    try:
        supabase.storage.from_("invoices").upload(
            path=f"{invoice_id}.pdf",
            file=pdf_bytes,
            file_options={"content-type": "application/pdf", "x-upsert": "true"}
        )
    except Exception as upload_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload invoice PDF: {str(upload_err)}"
        )

    # Generate signed URL
    try:
        signed_url_res = supabase.storage.from_("invoices").create_signed_url(f"{invoice_id}.pdf", 3600)
        return {"pdf_url": signed_url_res["signedURL"], "cached": False}
    except Exception as sign_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sign download URL: {str(sign_err)}"
        )

@router.post("/{invoice_id}/followup", response_model=FollowupWriterOutput)
@limiter.limit("60/minute")
def trigger_manual_followup(
    request: Request,
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Manually triggers the followup-writer agent to draft a reminder
    for a specific invoice. Verifies owner tenancy before execution.
    """
    user_id = current_user["id"]
    
    # 1. Retrieve invoice details
    try:
        res = supabase.table("invoices").select("*").eq("id", invoice_id).eq("user_id", user_id).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found or access denied"
            )
        invoice = res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch invoice details: {str(db_err)}"
        )

    # 2. Extract context values
    client_name = invoice.get("client_name") or "Client"
    project_title = invoice.get("project_title") or "Project"
    milestone_title = invoice.get("milestone_title") or "Milestone"
    total_amount = int(float(invoice.get("total_inr") or 0))
    
    # Calculate days overdue based on invoice due date
    due_date_str = invoice.get("due_date")
    if not due_date_str:
        days_overdue = 1
    else:
        try:
            # Parse due date (standard YYYY-MM-DD DATE format)
            due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
            today = datetime.date.today()
            days_overdue = (today - due_date).days
        except Exception:
            days_overdue = 1

    # 3. Execute agent task with exponential backoff
    try:
        followup_draft = run_agent_with_backoff(
            write_followup,
            client_name=client_name,
            project_title=project_title,
            total_amount=total_amount,
            days_overdue=days_overdue,
            milestone_title=milestone_title
        )
        return followup_draft
    except Exception as e:
        error_msg = str(e)
        input_desc = f"Invoice ID: {invoice_id} | Days Overdue: {days_overdue}"
        
        # Log failure to error logs table
        log_agent_error(
            user_id=user_id,
            agent_name="followup-writer",
            endpoint=f"/api/v1/invoices/{invoice_id}/followup",
            error_message=error_msg,
            input_snapshot=input_desc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent is taking longer than expected. We'll retry automatically. Error: {error_msg}"
        )
