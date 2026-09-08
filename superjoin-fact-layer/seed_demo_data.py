import uuid
import sqlite3
import os
from core.database import DB_PATH, init_db, insert_system_log

def seed_data():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear existing demo data
    cursor.execute("DELETE FROM relationships")
    cursor.execute("DELETE FROM facts")
    cursor.execute("DELETE FROM system_logs")
    conn.commit()

    # Fact IDs
    f1 = "f_delhivery_pincodes_2022"
    f2 = "f_delhivery_pincodes_fy24"
    f3 = "f_delhivery_rev_fy22"
    f4 = "f_delhivery_rev_fy24"
    f5 = "f_delhivery_hubs_stated"
    f6 = "f_delhivery_hubs_conflicting"
    f7 = "f_delhivery_ceo_2022"
    f8 = "f_delhivery_ceo_2024"
    f9 = "f_india_gdp_survey"
    f10 = "f_india_gdp_imf"
    f11 = "f_india_cpi_rbi"
    f12 = "f_india_cpi_survey"

    facts = [
        # --- DELHIVERY CORP ---
        (
            f1,
            "Operational Footprint",
            "Delhivery Limited",
            "covered pin codes across India reaching",
            "17,488 PIN codes",
            "As of December 31, 2021 (Prospectus disclosure)",
            "01-delhivery-prospectus-2022-excerpt.pdf",
            14,
            "As of December 31, 2021, our network covered 17,488 PIN codes across India, representing 90.0% of India's postal PIN codes."
        ),
        (
            f2,
            "Operational Footprint",
            "Delhivery Limited",
            "maintained nationwide network reach across",
            "Over 18,600 PIN codes",
            "Full Year FY2024 (Annual Report disclosure)",
            "02-delhivery-annual-report-fy24-excerpt.pdf",
            6,
            "During FY24, we further deepened direct reach to over 18,600 PIN codes across 28 states and all Union Territories."
        ),
        (
            f3,
            "Financial Performance",
            "Delhivery Limited",
            "reported revenue from contracts with customers of",
            "₹6,882.29 Crore",
            "Fiscal Year ended March 31, 2022 (Consolidated)",
            "01-delhivery-prospectus-2022-excerpt.pdf",
            28,
            "Revenue from contracts with customers for the Fiscal Year 2022 stood at ₹6,882.29 Cr compared to ₹3,646.53 Cr in Fiscal Year 2021."
        ),
        (
            f4,
            "Financial Performance",
            "Delhivery Limited",
            "reported consolidated revenue from operations of",
            "₹8,141.60 Crore",
            "Fiscal Year ended March 31, 2024 (Consolidated)",
            "02-delhivery-annual-report-fy24-excerpt.pdf",
            32,
            "Consolidated Revenue from operations grew to ₹8,141.60 Cr in FY2024, demonstrating resilient express volume expansion."
        ),
        (
            f5,
            "Infrastructure",
            "Delhivery Express Hubs",
            "operated automated mega sorting centres totaling",
            "24 automated mega hubs",
            "As of March 31, 2024 (Corporate infrastructure overview)",
            "02-delhivery-annual-report-fy24-excerpt.pdf",
            18,
            "Our automated infrastructure backbone comprises 24 automated mega sort centres across key commercial gateways."
        ),
        (
            f6,
            "Infrastructure",
            "Delhivery Express Hubs",
            "reported operating mega sorting centres count of",
            "21 automated mega hubs",
            "As of March 31, 2024 (Segmental operational annexure)",
            "03-delhivery-q4-fy24-earnings-presentation.pdf",
            11,
            "Network footprint as of Q4 FY24 includes 21 automated mega sorting facilities operational."
        ),
        (
            f7,
            "Corporate Governance",
            "Sahil Barua",
            "held executive leadership designation as",
            "Managing Director & Chief Executive Officer",
            "Calendar Year 2022 (IPO Prospectus executive roster)",
            "01-delhivery-prospectus-2022-excerpt.pdf",
            104,
            "Sahil Barua is the Managing Director and Chief Executive Officer of our Company, appointed effective May 1, 2021."
        ),
        (
            f8,
            "Corporate Governance",
            "Sahil Barua",
            "continued executive leadership designation as",
            "Managing Director & Chief Executive Officer",
            "Fiscal Year 2024 (Annual Report Board Report)",
            "02-delhivery-annual-report-fy24-excerpt.pdf",
            52,
            "Mr. Sahil Barua continued to steer the organization as Managing Director and CEO throughout FY 2023-24."
        ),

        # --- INDIA MACROECONOMY ---
        (
            f9,
            "Macroeconomic Growth",
            "Indian Economy Real GDP",
            "projected real GDP expansion rate at",
            "6.5% to 7.0%",
            "Financial Year 2024-25 baseline projection",
            "01-india-economic-survey-2024-25-excerpt.pdf",
            3,
            "The Survey conservatively projects real GDP growth of 6.5–7.0 per cent in FY25, acknowledging risks from global trade."
        ),
        (
            f10,
            "Macroeconomic Growth",
            "Indian Economy Real GDP",
            "forecasted real output expansion rate at",
            "7.0%",
            "Article IV Consultation Baseline for FY2024/25",
            "03-imf-india-2025-article-iv-excerpt.pdf",
            8,
            "Growth is projected to remain robust at 7.0 percent in FY2024/25, supported by sustained public infrastructure investment."
        ),
        (
            f11,
            "Monetary & Prices",
            "Headline CPI Inflation",
            "averaged annual retail price inflation of",
            "5.4%",
            "Financial Year 2023-24 (Audited average)",
            "02-rbi-annual-report-2024-25-excerpt.pdf",
            22,
            "Headline CPI inflation moderated to an average of 5.4 per cent during 2023-24 from 6.7 per cent in the preceding year."
        ),
        (
            f12,
            "Monetary & Prices",
            "Headline CPI Inflation",
            "recorded financial year average retail price rise of",
            "5.4%",
            "FY24 (Official statistics alignment)",
            "01-india-economic-survey-2024-25-excerpt.pdf",
            12,
            "Consumer Price Index (CPI) based retail inflation averaged 5.4 per cent in FY24, anchored by proactive supply measures."
        ),
    ]

    for f in facts:
        cursor.execute('''
            INSERT INTO facts (id, topic, subject, predicate, object_value, context, source_document, page_number, exact_quote)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', f)

    # Relationships
    relationships = [
        # Case 1: Corroboration 1 (Operational footprint)
        (
            str(uuid.uuid4()),
            f1,
            f2,
            "CORROBORATES",
            "Cross-document corroboration of delivery network breadth: Prospectus 2022 states reach of 17,488 PIN codes (~90% of India) and FY24 Annual Report confirms continuous high-density footprint (>18,600 PIN codes). Both validate Delhivery's expansive postal delivery coverage nationwide."
        ),
        # Case 1: Corroboration 2 (CPI inflation across independent economic institutions)
        (
            str(uuid.uuid4()),
            f11,
            f12,
            "CORROBORATES",
            "Cross-institutional consensus: The Reserve Bank of India (RBI Annual Report) and Ministry of Finance (Economic Survey 2024-25) corroborate exact identical FY24 headline retail inflation of 5.4%, demonstrating data integrity across sovereign reporting bodies."
        ),
        # Case 1: Corroboration 3 (Leadership continuity)
        (
            str(uuid.uuid4()),
            f7,
            f8,
            "CORROBORATES",
            "Executive continuity confirmed: The 2022 Prospectus and 2024 Annual Report both independently verify Sahil Barua's uninterrupted tenure as Managing Director & CEO."
        ),
        # Case 2: Genuine Contradiction (Infrastructure sort hubs)
        (
            str(uuid.uuid4()),
            f5,
            f6,
            "CONTRADICTS",
            "Genuine contradiction regarding physical sorting infrastructure: The FY24 Annual Report states 24 automated mega sort centres as of March 31, 2024, whereas the Q4 FY24 Earnings Presentation reports only 21 operational mega hubs for the exact same date without qualification."
        ),
        # Case 3: Reconciled Apparent Contradiction (Revenue growth across periods)
        (
            str(uuid.uuid4()),
            f3,
            f4,
            "RECONCILED",
            "Apparent contradiction in reported revenue numbers (₹6,882.29 Cr vs ₹8,141.60 Cr) is fully reconciled by temporal scope. The first figure represents full-year FY22 statutory disclosure, whereas the second represents audited FY24 performance, capturing two years of organic growth rather than conflicting accounts."
        ),
        # Case 3: Reconciled Apparent Contradiction (GDP growth forecast ranges vs point estimate)
        (
            str(uuid.uuid4()),
            f9,
            f10,
            "RECONCILED",
            "Apparent discrepancy between Economic Survey (6.5%–7.0%) and IMF Article IV (7.0%) is reconciled by forecasting methodology: the Economic Survey reports a prudential policy uncertainty band, while the IMF reports a point baseline estimate lying within the Survey's upper bound."
        ),
    ]

    for r in relationships:
        cursor.execute('''
            INSERT INTO relationships (id, fact_1_id, fact_2_id, relationship_type, reasoning)
            VALUES (?, ?, ?, ?, ?)
        ''', r)

    # Diagnostic & Extraction Failure Logs (Case 4)
    logs = [
        (
            str(uuid.uuid4()),
            "02-delhivery-annual-report-fy24-excerpt.pdf",
            "TABLE_PARSE_AMBIGUITY",
            "Page 45 multi-column non-standard matrix detected: Column 'FY23 Restated' lacked explicit bounding headers. Extractor flagged low confidence (<0.65) and logged isolated segment rather than injecting ungrounded numerical claims."
        ),
        (
            str(uuid.uuid4()),
            "03-delhivery-q4-fy24-earnings-presentation.pdf",
            "OCR_CHART_FRAGMENTATION",
            "Page 8 infographic on Express EBITDA yield contained vertical rotated metric annotations; successfully preserved surrounding context while logging raw token ambiguity."
        ),
        (
            str(uuid.uuid4()),
            "03-imf-india-2025-article-iv-excerpt.pdf",
            "CROSS_PERIOD_DENOMINATION_MISMATCH",
            "Table 2 fiscal balance figures mixed calendar-year aggregates with Indian fiscal year (Apr-Mar) timelines. Resolved via rule-based temporal tagging."
        ),
    ]

    for l in logs:
        cursor.execute('''
            INSERT INTO system_logs (id, document_name, log_type, message)
            VALUES (?, ?, ?, ?)
        ''', l)

    conn.commit()
    conn.close()
    print("[+] Successfully seeded enriched demonstration database with 12 grounded facts, 6 relationships, and diagnostic logs!")

if __name__ == "__main__":
    seed_data()
