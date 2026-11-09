from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def money(value):
    return f"{value:,.2f}"


def lines_to_html(lines):
    return "<br/>".join(escape(line) for line in lines if line and line.strip())


def build_invoice_pdf(invoice):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Invoice {invoice.number}",
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = ParagraphStyle("heading", parent=styles["Title"], alignment=0)
    story = []

    story.append(Paragraph(f"Invoice {invoice.number}", heading))
    story.append(
        Paragraph(
            f"Issued: {invoice.issue_date:%d %b %Y} &nbsp;&nbsp; "
            f"Due: {invoice.due_date:%d %b %Y} &nbsp;&nbsp; "
            f"Status: {escape(invoice.status_label)} &nbsp;&nbsp; "
            f"Currency: {invoice.currency}",
            normal,
        )
    )
    story.append(Spacer(1, 8 * mm))

    owner = invoice.owner
    from_lines = [owner.get_full_name() or owner.username, owner.email]
    client = invoice.client
    client_lines = [client.name, client.email, client.phone] + client.address.splitlines()
    parties = Table(
        [
            [
                Paragraph(f"<b>From</b><br/>{lines_to_html(from_lines)}", normal),
                Paragraph(f"<b>Bill to</b><br/>{lines_to_html(client_lines)}", normal),
            ]
        ],
        colWidths=[85 * mm, 85 * mm],
    )
    parties.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(parties)
    story.append(Spacer(1, 8 * mm))

    rows = [["Description", "Qty", "Unit price", "Amount"]]
    for item in invoice.items.all():
        rows.append(
            [
                Paragraph(escape(item.description), normal),
                money(item.quantity),
                money(item.unit_price),
                money(item.total),
            ]
        )
    first_total_row = len(rows)
    rows.append(["", "", "Subtotal", money(invoice.subtotal)])
    rows.append(["", "", f"Tax ({invoice.tax_rate}%)", money(invoice.tax_amount)])
    rows.append(["", "", f"Total ({invoice.currency})", money(invoice.total)])

    table = Table(rows, colWidths=[90 * mm, 20 * mm, 30 * mm, 30 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f2f5")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, first_total_row - 1), 0.5, colors.lightgrey),
                ("LINEABOVE", (2, first_total_row), (-1, first_total_row), 0.75, colors.grey),
                ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(table)

    if invoice.notes.strip():
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph("<b>Notes</b>", normal))
        story.append(Paragraph(escape(invoice.notes).replace("\n", "<br/>"), normal))

    doc.build(story)
    return buffer.getvalue()