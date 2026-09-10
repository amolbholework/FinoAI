import io

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _category_chart(breakdown_minor: dict[str, int]) -> Drawing:
    drawing = Drawing(400, 200)
    chart = VerticalBarChart()
    chart.x = 30
    chart.y = 20
    chart.width = 340
    chart.height = 150

    items = sorted(breakdown_minor.items(), key=lambda kv: -kv[1])[:8]
    chart.data = [[v / 100 for _, v in items]]
    chart.categoryAxis.categoryNames = [k for k, _ in items]
    chart.categoryAxis.labels.angle = 30
    chart.categoryAxis.labels.dy = -10
    chart.bars[0].fillColor = colors.HexColor("#047857")
    drawing.add(chart)
    return drawing


def build_monthly_summary_pdf(summary: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"FinPilot AI — Monthly Summary: {summary['month']}", styles["Title"]))
    story.append(Spacer(1, 12))

    totals_table = Table(
        [
            ["Total spend", f"₹{summary['total_spend_minor'] / 100:,.2f}"],
            ["Income", f"₹{summary['income_minor'] / 100:,.2f}"],
            ["Net", f"₹{summary['net_minor'] / 100:,.2f}"],
            ["Savings rate", f"{summary['savings_rate_pct']}%"],
        ],
        colWidths=[150, 150],
    )
    totals_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ]
        )
    )
    story.append(totals_table)
    story.append(Spacer(1, 20))

    if summary["category_breakdown_minor"]:
        story.append(Paragraph("Spend by category", styles["Heading2"]))
        story.append(_category_chart(summary["category_breakdown_minor"]))
        story.append(Spacer(1, 12))

        rows = [["Category", "Spend"]] + [
            [cat, f"₹{amt / 100:,.2f}"]
            for cat, amt in sorted(summary["category_breakdown_minor"].items(), key=lambda kv: -kv[1])
        ]
        cat_table = Table(rows, colWidths=[220, 120])
        cat_table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8F9FB")),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ]
            )
        )
        story.append(cat_table)

    doc.build(story)
    return buffer.getvalue()
