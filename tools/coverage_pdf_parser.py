# C:\office_crm\tools\coverage_pdf_parser.py

import json
import re
from datetime import datetime
from pathlib import Path

import pdfplumber


BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG_DIR = BASE_DIR / "debug_pdf"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

DEBUG_PDF_PARSE = True


KNOWN_INSURERS = [
    "메리츠화재",
    "삼성화재",
    "현대해상",
    "DB손해보험",
    "DB손보",
    "KB손해보험",
    "한화손해보험",
    "흥국화재",
    "롯데손해보험",
    "롯데손보",
    "MG손해보험",
    "NH농협손해보험",
    "농협손해보험",
    "AIG손해보험",
    "하나손해보험",
    "하나손보",
    "캐롯손해보험",
    "악사손해보험",
    "AXA손해보험",
    "삼성생명",
    "한화생명",
    "교보생명",
    "신한라이프",
    "동양생명",
    "미래에셋생명",
    "NH농협생명",
    "농협생명",
    "흥국생명",
    "ABL생명",
    "KDB생명",
    "푸본현대생명",
    "라이나생명",
    "처브라이프생명",
    "메트라이프생명",
    "AIA생명",
]


INSURER_ALIASES = {
    "DB손보": "DB손해보험",
    "롯데손보": "롯데손해보험",
    "하나손보": "하나손해보험",
    "농협손해보험": "NH농협손해보험",
    "농협생명": "NH농협생명",
    "AXA손해보험": "악사손해보험",
}


def clean_text(value):
    text = str(value or "")
    text = text.replace("\u00a0", " ")
    text = text.replace("_x000D_", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def normalize_join(value):
    return re.sub(r"\s+", "", str(value or "")).strip()


def save_debug_json(name, data):
    if not DEBUG_PDF_PARSE:
        return

    try:
        path = DEBUG_DIR / f"{name}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[PDF DEBUG 저장] {path}")

    except Exception as e:
        print(f"[PDF DEBUG 저장 실패] {name}: {e}")


def normalize_insurer_name(value):
    value = clean_text(value)
    return INSURER_ALIASES.get(value, value)


def extract_insurer_name(text):
    text = clean_text(text)
    matches = []

    for insurer in KNOWN_INSURERS:
        if insurer in text:
            matches.append(insurer)

    if not matches:
        return ""

    matches = sorted(matches, key=len, reverse=True)
    return normalize_insurer_name(matches[0])


def amount_to_number(value):
    text = clean_text(value).replace(",", "")

    if not text:
        return 0

    match = re.search(r"([\d.]+)\s*(억|천만|백만|만|원)?", text)

    if not match:
        return 0

    num = float(match.group(1))
    unit = match.group(2) or ""

    if unit == "억":
        return int(num * 100000000)
    if unit == "천만":
        return int(num * 10000000)
    if unit == "백만":
        return int(num * 1000000)
    if unit == "만":
        return int(num * 10000)

    return int(num)


def extract_pdf_pages(pdf_path):
    pdf_path = Path(pdf_path)
    pages = []
    debug_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            lines = [
                clean_text(line)
                for line in text.splitlines()
                if clean_text(line)
            ]

            tables = []

            try:
                raw_tables = page.extract_tables() or []

                for table in raw_tables:
                    clean_table = []

                    for raw_row in table or []:
                        row = [clean_text(cell) for cell in (raw_row or [])]

                        if any(row):
                            clean_table.append(row)

                    if clean_table:
                        tables.append(clean_table)

            except Exception as e:
                print(f"[PDF TABLE 추출 실패] page={page_no}, error={e}")
                tables = []

            save_debug_json(
                f"{debug_run_id}_page_{page_no}_text",
                {"page_no": page_no, "text": text},
            )

            save_debug_json(
                f"{debug_run_id}_page_{page_no}_lines",
                {"page_no": page_no, "lines": lines},
            )

            save_debug_json(
                f"{debug_run_id}_page_{page_no}_tables",
                {"page_no": page_no, "tables": tables},
            )

            pages.append(
                {
                    "page_no": page_no,
                    "lines": lines,
                    "tables": tables,
                    "raw_text": text,
                }
            )

    return pages


def parse_customer_info(first_page_lines):
    joined = " ".join(first_page_lines)

    result = {
        "customer_name": "",
        "age": "",
        "gender": "",
        "total_contracts": "",
        "monthly_premium": "",
        "created_at": "",
    }

    m = re.search(r"(.+?)\((\d+)세\s*,\s*(남자|여자)\)님의", joined)

    if m:
        result["customer_name"] = clean_text(m.group(1))
        result["age"] = m.group(2)
        result["gender"] = m.group(3)

    m = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", joined)

    if m:
        result["created_at"] = m.group(1)

    m = re.search(r"월 보험료\s*([\d,]+)\s*원", joined)

    if m:
        result["monthly_premium"] = m.group(1)

    if not result["monthly_premium"]:
        money_candidates = re.findall(r"([\d,]{5,})", joined)

        if money_candidates:
            result["monthly_premium"] = money_candidates[-1]

    m = re.search(r"정상계약\s*(\d+)\s*건", joined)

    if m:
        result["total_contracts"] = m.group(1)

    return result


def merge_multiline_contract_lines(lines):
    merged = []
    buffer = ""

    for raw_line in lines:
        line = clean_text(raw_line)

        if not line:
            continue

        if re.match(r"^\d+\s+", line):
            if buffer:
                merged.append(buffer)

            buffer = line
            continue

        if buffer:
            buffer = f"{buffer} {line}"
        else:
            buffer = line

    if buffer:
        merged.append(buffer)

    return merged


def parse_contract_list(first_page_lines):
    contracts = []
    merged_lines = merge_multiline_contract_lines(first_page_lines)

    for line in merged_lines:
        line = clean_text(line)

        if not re.match(r"^\d+\s+", line):
            continue

        if "월납" not in line and "년납" not in line:
            continue

        insurer = extract_insurer_name(line)

        if not insurer:
            continue

        after_insurer = line.split(insurer, 1)[-1].strip()

        m = re.search(
            r"(?P<product>.+?)\s+"
            r"(?P<contract_date>\d{4}-\d{2}-\d{2})\s+"
            r"(?P<pay_cycle>월납|년납)\s+"
            r"(?P<pay_period>\S+)\s+"
            r"(?P<maturity>\S+)\s+"
            r"(?P<premium>[\d,]+원)",
            after_insurer,
        )

        if not m:
            continue

        no_match = re.match(r"^(?P<no>\d+)", line)

        data = m.groupdict()
        data["no"] = no_match.group("no") if no_match else ""
        data["insurer"] = insurer
        data["company"] = insurer
        data["보험사"] = insurer
        data["product"] = clean_text(data["product"])
        data["product_name"] = data["product"]
        data["상품명"] = data["product"]
        data["contract_date"] = data["contract_date"]
        data["가입시기"] = data["contract_date"]
        data["premium_number"] = amount_to_number(data["premium"])

        contracts.append(data)

    return contracts


def detect_product_header(lines, previous_context=None):
    previous_context = previous_context or {}

    insurer = ""
    contract_date = ""
    product_name = ""
    premium = ""

    for idx, line in enumerate(lines[:20]):
        line = clean_text(line)
        found_insurer = extract_insurer_name(line)

        if not found_insurer:
            continue

        insurer = found_insurer

        m = re.search(r"가입일자\s*:\s*(\d{4}-\d{2}-\d{2})", line)

        if m:
            contract_date = m.group(1)

        product_candidates = []

        for next_line in lines[idx + 1: idx + 5]:
            next_line = clean_text(next_line)

            if not next_line:
                continue

            if re.search(r"^\d+\s+(정액|실손)\s+", next_line):
                break

            if re.search(r"\d{4}-\d{2}-\d{2}~\d{4}-\d{2}-\d{2}", next_line):
                break

            if "월납" in next_line or "년납" in next_line:
                break

            if "호남GA" in next_line:
                break

            product_candidates.append(next_line)

        product_name = clean_text(" ".join(product_candidates))
        break

    joined = " ".join(lines[:20])

    if not insurer:
        insurer = extract_insurer_name(joined)

    if not contract_date:
        m = re.search(r"가입일자\s*:\s*(\d{4}-\d{2}-\d{2})", joined)

        if m:
            contract_date = m.group(1)

    m = re.search(r"([\d,]+원)", joined)

    if m:
        premium = m.group(1)

    if not insurer:
        insurer = previous_context.get("보험사", "") or previous_context.get("company", "")

    if not contract_date:
        contract_date = previous_context.get("가입시기", "") or previous_context.get("contract_date", "")

    if not product_name:
        product_name = previous_context.get("상품명", "") or previous_context.get("product_name", "")

    if not premium:
        premium = previous_context.get("premium", "")

    return {
        "insurer": insurer,
        "company": insurer,
        "보험사": insurer,
        "contract_date": contract_date,
        "가입시기": contract_date,
        "product_name": product_name,
        "product": product_name,
        "상품명": product_name,
        "premium": premium,
        "premium_number": amount_to_number(premium),
    }


def parse_coverage_row_tokens(line):
    line = clean_text(line)

    m = re.match(
        r"^(?P<no>\d+)\s+"
        r"(?P<pay_type>정액|실손)\s+"
        r"(?P<body>.+?)\s+"
        r"(?P<amount>[\d,]+(?:억|천만|백만|만|원)?)$",
        line,
    )

    if not m:
        return None

    no = m.group("no")
    pay_type = m.group("pay_type")
    body = clean_text(m.group("body"))
    amount = clean_text(m.group("amount"))

    if not body:
        return None

    company_coverage_name = ""
    credit_coverage_name = ""

    known_credit_patterns = [
        "기타 인보험(정액)담보",
        "교통사고 처리지원금(6주미만 진단)",
        "자동차사고 변호사선임비용",
        "교통사고 벌금(대물)",
        "교통사고 벌금(대인)",
        "상급종합병원 질병입원일당",
        "상급종합병원 상해입원일당",
        "종합병원이하 질병입원일당",
        "종합병원이하 상해입원일당",
        "질병 간호·간병통합서비스사용일당",
        "상해 간호·간병통합서비스사용일당",
        "항암방사선약물치료비",
        "고액항암치료비",
        "소액암진단(유사암진단)",
        "암진단(유병자)",
        "상해사망(유병자)",
        "질병수술(유병자)",
        "질병종수술",
        "상해종수술",
        "상해사망",
        "상해후유장해",
        "질병입원일당",
        "상해입원일당",
        "간병인질병입원일당",
        "간병인상해입원일당",
        "상해중환자실입원일당",
        "교통상해입원일당",
        "골절진단",
        "중대골절진단",
        "화상진단",
        "골절수술",
        "화상수술",
        "특정상해수술",
        "상해수술",
        "암수술",
        "뇌혈관질환진단",
        "허혈성심장질환진단",
        "뇌혈관질환수술",
        "허혈성심장질환수술",
        "특정질병진단",
        "특정질병수술",
        "기타수술",
        "깁스치료",
        "교통상해사망",
        "화재벌금담보",
        "가전제품고장수리비용",
        "자동차사고부상위로금",
        "과실치사상 벌금",
        "업무상과실 중과실치사상 벌금",
        "가족생활배상책임",
        "특정질병사망",
        "특정상해사망",
        "특정질병후유장해",
        "특정상해후유장해",
        "특정상해진단",
        "특정질병진단",
        "특정상해입원일당",
        "기타입원일당",
        "농업작업안전 재해 및 질병입원의료비",
        "농업작업안전 재해 및 질병처방조제료",
        "농업작업안전 재해 및 질병외래의료비",
        "상해(일반상해,전체상해를 의미)입원의료비",
        "상해(일반상해,전체상해를 의미)처방조제료",
        "상해(일반상해,전체상해를 의미)외래의료비",
        "질병(전체질병을 의미)입원의료비",
        "질병(전체질병을 의미)처방조제료",
        "질병(전체질병을 의미)외래의료비",
    ]

    for pattern in sorted(known_credit_patterns, key=len, reverse=True):
        if body.endswith(pattern):
            credit_coverage_name = pattern
            company_coverage_name = clean_text(body[: -len(pattern)])
            break

    if not company_coverage_name and not credit_coverage_name:
        parts = body.split()

        if len(parts) >= 2:
            credit_coverage_name = parts[-1]
            company_coverage_name = clean_text(" ".join(parts[:-1]))
        else:
            company_coverage_name = body
            credit_coverage_name = ""

    if not company_coverage_name:
        company_coverage_name = body

    display_name = company_coverage_name or credit_coverage_name or body

    return {
        "no": no,
        "pay_type": pay_type,
        "company_coverage_name": company_coverage_name,
        "회사담보명": company_coverage_name,
        "credit_coverage_name": credit_coverage_name,
        "신정원담보명": credit_coverage_name,
        "coverage_name": display_name,
        "담보명": display_name,
        "category": credit_coverage_name,
        "amount": amount,
        "보장금액": amount,
        "amount_number": amount_to_number(amount),
    }


def parse_coverage_rows_from_lines(lines, page_no, product_info):
    rows = []

    for line in lines:
        line = clean_text(line)

        if not re.match(r"^\d+\s+(정액|실손)\s+", line):
            continue

        parsed = parse_coverage_row_tokens(line)

        if not parsed:
            continue

        row = {
            "page_no": page_no,
            **parsed,
            **product_info,
        }

        rows.append(row)

    return rows


def parse_coverage_rows_from_tables(tables, page_no, product_info):
    rows = []

    for table_index, table in enumerate(tables):
        if not table:
            continue

        for raw_row in table:
            row_values = [clean_text(v) for v in raw_row if clean_text(v)]

            if len(row_values) < 5:
                continue

            no = row_values[0]
            pay_type = row_values[1]
            company_coverage_name = row_values[2]
            credit_coverage_name = row_values[3]
            amount = row_values[4]

            if not str(no).isdigit():
                continue

            if pay_type not in ["정액", "실손"]:
                continue

            result = {
                "page_no": page_no,
                "no": no,
                "pay_type": pay_type,
                "company_coverage_name": company_coverage_name,
                "회사담보명": company_coverage_name,
                "credit_coverage_name": credit_coverage_name,
                "신정원담보명": credit_coverage_name,
                "coverage_name": company_coverage_name,
                "담보명": company_coverage_name,
                "category": credit_coverage_name,
                "amount": amount,
                "보장금액": amount,
                "amount_number": amount_to_number(amount),
                **product_info,
            }

            rows.append(result)

    save_debug_json(
        f"page_{page_no}_table_rows_direct",
        {"page_no": page_no, "rows": rows},
    )

    return rows


def parse_coverage_rows_from_page(page, previous_context=None):
    page_no = page["page_no"]
    lines = page["lines"]
    tables = page["tables"]

    product_info = detect_product_header(
        lines=lines,
        previous_context=previous_context,
    )

    save_debug_json(
        f"page_{page_no}_product_info",
        {
            "page_no": page_no,
            "product_info": product_info,
            "header_lines": lines[:20],
        },
    )

    rows_from_tables = parse_coverage_rows_from_tables(
        tables=tables,
        page_no=page_no,
        product_info=product_info,
    )

    rows_from_lines = parse_coverage_rows_from_lines(
        lines=lines,
        page_no=page_no,
        product_info=product_info,
    )

    save_debug_json(
        f"page_{page_no}_parsed_compare",
        {
            "page_no": page_no,
            "rows_from_tables_count": len(rows_from_tables),
            "rows_from_lines_count": len(rows_from_lines),
            "rows_from_tables": rows_from_tables,
            "rows_from_lines": rows_from_lines,
        },
    )

    if rows_from_tables:
        return rows_from_tables, product_info

    return rows_from_lines, product_info


def build_contracts_from_coverages(coverages):
    seen = set()
    contracts = []

    for row in coverages:
        company = row.get("보험사", "") or row.get("company", "") or row.get("insurer", "")
        product = row.get("상품명", "") or row.get("product", "") or row.get("product_name", "")
        contract_date = row.get("가입시기", "") or row.get("contract_date", "")
        premium = row.get("premium", "")
        premium_number = row.get("premium_number", 0)

        key = (company, product, contract_date, premium)

        if not company and not product and not contract_date:
            continue

        if key in seen:
            continue

        seen.add(key)

        contracts.append(
            {
                "no": str(len(contracts) + 1),
                "보험사": company,
                "company": company,
                "insurer": company,
                "상품명": product,
                "product": product,
                "product_name": product,
                "가입시기": contract_date,
                "contract_date": contract_date,
                "premium": premium,
                "premium_number": premium_number,
            }
        )

    return contracts


def classify_coverage(row):
    text = " ".join(
        [
            str(row.get("company_coverage_name", "")),
            str(row.get("credit_coverage_name", "")),
            str(row.get("coverage_name", "")),
            str(row.get("category", "")),
        ]
    )

    rules = [
        ("일반암 진단비", ["암진단", "유사암제외"]),
        ("유사암 진단비", ["유사암진단", "유사암"]),
        ("뇌혈관 진단비", ["뇌혈관질환진단", "뇌혈관질환진단비", "뇌혈관"]),
        ("허혈성심장질환 진단비", ["허혈성심질환진단", "허혈성심장질환진단", "허혈성"]),
        ("뇌혈관 수술비", ["뇌혈관질환수술"]),
        ("허혈성심장질환 수술비", ["허혈성심질환수술", "허혈성심장질환수술"]),
        ("항암방사선치료비", ["항암방사선"]),
        ("항암약물치료비", ["항암약물"]),
        ("표적항암치료비", ["표적항암"]),
        ("면역항암치료비", ["면역항암"]),
        ("중입자치료비", ["중입자"]),
        ("양성자치료비", ["양성자"]),
        ("세기조절방사선치료비", ["세기조절"]),
        ("상해사망", ["상해사망"]),
        ("질병수술비", ["질병수술"]),
        ("상해수술비", ["상해수술"]),
        ("질병입원일당", ["질병입원일당", "질병입원비"]),
        ("상해입원일당", ["상해입원일당", "상해입원비"]),
        ("간병인 입원일당", ["간병인"]),
        ("운전자 담보", ["교통사고", "자동차사고", "벌금", "변호사", "처리지원금"]),
        ("실손의료비", ["입원의료비", "외래의료비", "처방조제료", "실손"]),
        ("후유장해", ["후유장해"]),
        ("골절/화상", ["골절", "화상"]),
    ]

    for label, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return label

    return "미분류"


def parse_coverage_pdf(pdf_path):
    pages = extract_pdf_pages(pdf_path)

    if not pages:
        return {
            "customer": {},
            "contracts": [],
            "coverages": [],
            "summary": [],
        }

    first_page_lines = pages[0]["lines"]

    customer = parse_customer_info(first_page_lines)
    contracts_from_first_page = parse_contract_list(first_page_lines)

    coverages = []
    previous_context = {}

    for page in pages[1:]:
        page_rows, page_context = parse_coverage_rows_from_page(
            page=page,
            previous_context=previous_context,
        )

        coverages.extend(page_rows)

        if page_context.get("보험사") or page_context.get("상품명") or page_context.get("가입시기"):
            previous_context = page_context

    for row in coverages:
        row["mapped_category"] = classify_coverage(row)

    contracts_from_coverages = build_contracts_from_coverages(coverages)

    contracts = contracts_from_first_page

    if len(contracts_from_coverages) > len(contracts_from_first_page):
        contracts = contracts_from_coverages

    summary_map = {}

    for row in coverages:
        category = row["mapped_category"]

        if category not in summary_map:
            summary_map[category] = {
                "분류": category,
                "가입금액합계": 0,
                "담보수": 0,
                "대표담보": [],
            }

        summary_map[category]["가입금액합계"] += row.get("amount_number", 0)
        summary_map[category]["담보수"] += 1

        name = row.get("company_coverage_name") or row.get("coverage_name", "")

        if name and len(summary_map[category]["대표담보"]) < 5:
            summary_map[category]["대표담보"].append(name)

    summary = []

    for item in summary_map.values():
        item["대표담보"] = " / ".join(item["대표담보"])
        summary.append(item)

    summary = sorted(summary, key=lambda x: x["분류"])

    result = {
        "customer": customer,
        "contracts": contracts,
        "coverages": coverages,
        "summary": summary,
    }

    save_debug_json("final_parsed_result", result)

    print("=" * 80)
    print("[PDF PARSER 최종 요약]")
    print(f"contracts_from_first_page: {len(contracts_from_first_page)}건")
    print(f"contracts_from_coverages: {len(contracts_from_coverages)}건")
    print(f"contracts_final: {len(contracts)}건")
    print(f"coverages: {len(coverages)}건")
    print(f"debug_dir: {DEBUG_DIR}")
    print("=" * 80)

    return result