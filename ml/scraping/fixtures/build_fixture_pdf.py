"""
Builds a fixture PDF that mirrors the real structure of AFCARS Report #29's
"Numbers at a Glance" table (U.S. Administration for Children and Families,
a public government document). The numbers below are the actual published
figures from that report, used here to prove the scraper/PDF-parser
pipeline against a realistic table shape without requiring live internet
access from this sandboxed environment (see ml/scraping/scraper.py
docstring for the network limitation this works around).
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

doc = SimpleDocTemplate("/home/claude/mock_gov_site/afcars-report-fixture.pdf", pagesize=letter)

# Real published figures from AFCARS Report #29 (Numbers at a Glance table)
data = [
    ["Fiscal Year", "2017", "2018", "2019", "2020", "2021"],
    ["Number in foster care on September 30 of the FY", "436,556", "437,337", "426,325", "407,318", "391,098"],
    ["Number entered foster care during the FY", "270,197", "263,776", "252,414", "216,842", "206,812"],
    ["Number exited foster care during the FY", "248,882", "252,209", "249,936", "224,425", "214,971"],
    ["Number served by the foster care system during the FY", "685,403", "689,505", "676,188", "631,686", "606,031"],
    ["Number waiting to be adopted on September 30 of the FY", "124,004", "126,546", "123,823", "117,446", "113,589"],
]

table = Table(data, colWidths=[3.2 * inch] + [0.62 * inch] * 5)
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3a7ca5")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))

story = [
    Paragraph("The AFCARS Report - Preliminary FY 2021 Estimates (No. 29)", styles["Title"]),
    Spacer(1, 12),
    Paragraph(
        "SOURCE: Adoption and Foster Care Analysis and Reporting System (AFCARS) FY 2021 data. "
        "U.S. Department of Health and Human Services, Administration for Children and Families, "
        "Administration on Children, Youth and Families, Children's Bureau.",
        styles["Normal"],
    ),
    Spacer(1, 20),
    Paragraph("Numbers at a Glance", styles["Heading2"]),
    Spacer(1, 8),
    table,
]

doc.build(story)
print("Fixture PDF built.")
