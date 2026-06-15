import json
from difflib import SequenceMatcher

from tools.ollama_client import is_ollama_available, ask_ollama_json
from tools.coverage_mapping_store import find_saved_mapping


DEFAULT_TARGET_COVERAGES = [
    "일반암진단비",
    "유사암진단비",
    "고액암진단비",
    "뇌혈관질환진단비",
    "뇌졸중진단비",
    "뇌출혈진단비",
    "허혈성심장질환진단비",
    "급성심근경색진단비",
    "질병수술비",
    "상해수술비",
    "1-5종수술비",
    "1-7종수술비",
    "항암약물치료비",
    "항암방사선치료비",
    "표적항암약물허가치료비",
    "실손의료비",
]


TARGET_KEYWORDS = {
    "일반암진단비": ["일반암", "암진단", "암진단비", "암진단급여금"],
    "유사암진단비": ["유사암", "소액암", "갑상선암", "기타피부암", "제자리암", "경계성종양"],
    "고액암진단비": ["고액암", "특정암", "5대고액암", "10대고액암"],
    "뇌혈관질환진단비": ["뇌혈관", "뇌혈관질환"],
    "뇌졸중진단비": ["뇌졸중"],
    "뇌출혈진단비": ["뇌출혈"],
    "허혈성심장질환진단비": ["허혈성", "허혈성심장", "허혈성심질환", "협심증"],
    "급성심근경색진단비": ["급성심근경색", "심근경색"],
    "질병수술비": ["질병수술"],
    "상해수술비": ["상해수술"],
    "1-5종수술비": ["1-5종", "1~5종", "5종수술", "1종", "2종", "3종", "4종", "5종"],
    "1-7종수술비": ["1-7종", "1~7종", "7종수술"],
    "항암약물치료비": ["항암약물", "항암치료", "항암 약물"],
    "항암방사선치료비": ["항암방사선", "방사선치료", "항암 방사선"],
    "표적항암약물허가치료비": ["표적항암", "표적항암약물", "허가치료"],
    "실손의료비": ["실손", "실비", "의료비"],
}


COMPANY_KEYS = ["보험사", "company", "insurer", "회사", "보험회사"]
PRODUCT_KEYS = ["상품명", "product", "product_name", "상품"]
DATE_KEYS = ["가입시기", "contract_date", "계약일자", "가입일", "시작일", "계약일"]
RENEWAL_KEYS = ["갱신주기", "갱신", "보험기간", "납입기간", "renewal"]
COMPANY_COVERAGE_KEYS = ["회사담보명", "company_coverage_name", "회사 담보명"]
CREDIT_COVERAGE_KEYS = ["신정원담보명", "credit_coverage_name", "신정원 담보명"]
COVERAGE_KEYS = ["담보명", "coverage_name", "특약명", "보장명", "name", "담보", "특약"]
AMOUNT_KEYS = ["보장금액", "amount", "가입금액", "보험가입금액", "금액"]


AUTO_MATCH_SCORE = 85.0
AI_ANALYZE_MIN_SCORE = 30.0
AI_AUTO_CONFIDENCE = 0.85
AI_CHECK_CONFIDENCE = 0.60


def normalize_text(value):
    text = str(value or "")

    for ch in [" ", "\n", "\t", "\r", "-", "_", "(", ")", "[", "]", "{", "}", "/", "\\", ",", ".", ":", ";", "·", "ㆍ"]:
        text = text.replace(ch, "")

    return text.strip().lower()


def clean_text(value):
    return str(value or "").strip()


def clean_recommend_label(value):
    label = clean_text(value)
    if label == "매핑 제외":
        return ""
    return label


def get_first_value(data, keys, default=""):
    if not isinstance(data, dict):
        return default

    for key in keys:
        value = data.get(key)
        if value not in [None, ""]:
            return value

    return default


def similarity(a, b):
    a = normalize_text(a)
    b = normalize_text(b)

    if not a or not b:
        return 0.0

    return round(SequenceMatcher(None, a, b).ratio() * 100, 1)


def build_match_text(company_coverage_name, credit_coverage_name, source_name):
    return " ".join(
        [
            str(company_coverage_name or ""),
            str(credit_coverage_name or ""),
            str(source_name or ""),
        ]
    ).strip()


def keyword_score(match_text, target_label):
    source_norm = normalize_text(match_text)
    target_norm = normalize_text(target_label)

    if not source_norm or not target_norm:
        return 0.0

    score = similarity(match_text, target_label)

    for keyword in TARGET_KEYWORDS.get(target_label, []):
        keyword_norm = normalize_text(keyword)
        if keyword_norm and keyword_norm in source_norm:
            score += 35

    if target_norm and target_norm in source_norm:
        score += 25

    if source_norm and source_norm in target_norm:
        score += 10

    if "유사암" in source_norm and target_label == "일반암진단비":
        score -= 60
    if "갑상선암" in source_norm and target_label == "일반암진단비":
        score -= 50
    if "기타피부암" in source_norm and target_label == "일반암진단비":
        score -= 50
    if "제자리암" in source_norm and target_label == "일반암진단비":
        score -= 50
    if "경계성종양" in source_norm and target_label == "일반암진단비":
        score -= 50
    if "상해" in source_norm and target_label == "질병수술비":
        score -= 45
    if "질병" in source_norm and target_label == "상해수술비":
        score -= 45

    return max(0.0, min(round(score, 1), 100.0))


def rule_based_recommend(match_text, target_coverages):
    candidates = []

    for target in target_coverages:
        score = keyword_score(match_text, target)
        candidates.append({"target": target, "score": score})

    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    if not candidates:
        return "", 0.0

    best = candidates[0]

    # 30점 미만이어도 행 자체를 제외하지 않는다.
    # 추천위치는 비워두고 상태는 decide_final_mapping()에서 확인필요로 보낸다.
    if best["score"] < AI_ANALYZE_MIN_SCORE:
        return "", best["score"]

    return best["target"], best["score"]


def extract_contracts_from_parsed_data(parsed_data):
    if not isinstance(parsed_data, dict):
        return []

    for key in ["contracts", "contract_list", "계약정보", "계약", "policies", "policy_list"]:
        value = parsed_data.get(key)
        if isinstance(value, list):
            return value

    return []


def extract_coverages_from_parsed_data(parsed_data):
    if not parsed_data:
        return []

    if isinstance(parsed_data, dict):
        for key in ["coverages", "coverage_list", "담보", "담보상세", "items", "benefits", "특약", "보장"]:
            value = parsed_data.get(key)
            if isinstance(value, list):
                return value

    if isinstance(parsed_data, list):
        return parsed_data

    return []


def build_default_contract_context(parsed_data):
    contracts = extract_contracts_from_parsed_data(parsed_data)

    if not contracts or not isinstance(contracts[0], dict):
        return {"보험사": "", "상품명": "", "가입시기": "", "갱신주기": ""}

    first = contracts[0]

    return {
        "보험사": get_first_value(first, COMPANY_KEYS),
        "상품명": get_first_value(first, PRODUCT_KEYS),
        "가입시기": get_first_value(first, DATE_KEYS),
        "갱신주기": get_first_value(first, RENEWAL_KEYS),
    }


def normalize_extracted_rows(parsed_data):
    extracted = extract_coverages_from_parsed_data(parsed_data)
    default_context = build_default_contract_context(parsed_data)

    rows = []

    for idx, item in enumerate(extracted):
        if isinstance(item, dict):
            company_coverage_name = get_first_value(item, COMPANY_COVERAGE_KEYS)
            credit_coverage_name = get_first_value(item, CREDIT_COVERAGE_KEYS)
            source_name = get_first_value(item, COVERAGE_KEYS)
            amount = get_first_value(item, AMOUNT_KEYS)

            if not source_name:
                source_name = company_coverage_name or credit_coverage_name

            company = get_first_value(item, COMPANY_KEYS, default_context.get("보험사", ""))
            product = get_first_value(item, PRODUCT_KEYS, default_context.get("상품명", ""))
            contract_date = get_first_value(item, DATE_KEYS, default_context.get("가입시기", ""))
            renewal = get_first_value(item, RENEWAL_KEYS, default_context.get("갱신주기", ""))
        else:
            company_coverage_name = str(item)
            credit_coverage_name = ""
            source_name = str(item)
            amount = ""
            company = default_context.get("보험사", "")
            product = default_context.get("상품명", "")
            contract_date = default_context.get("가입시기", "")
            renewal = default_context.get("갱신주기", "")

        if not source_name and not company_coverage_name and not credit_coverage_name:
            continue

        match_text = build_match_text(company_coverage_name, credit_coverage_name, source_name)

        rows.append(
            {
                "row_id": idx,
                "보험사": company,
                "상품명": product,
                "가입시기": contract_date,
                "갱신주기": renewal,
                "회사담보명": company_coverage_name,
                "신정원담보명": credit_coverage_name,
                "추출담보명": source_name,
                "매칭검토문구": match_text,
                "보장금액": amount,
            }
        )

    return rows


def ai_batch_recommend(ai_targets, target_coverages, model="qwen2.5:7b", chunk_size=10):
    if not ai_targets:
        return {}

    if not is_ollama_available():
        print("[AI 일괄매핑] Ollama 연결 불가")
        return {}

    all_output = {}

    for start in range(0, len(ai_targets), chunk_size):
        chunk = ai_targets[start:start + chunk_size]

        compact_items = []

        for row in chunk:
            compact_items.append(
                {
                    "row_id": row["row_id"],
                    "보험사": row.get("보험사", ""),
                    "상품명": row.get("상품명", ""),
                    "회사담보명": row.get("회사담보명", ""),
                    "신정원담보명": row.get("신정원담보명", ""),
                    "추출담보명": row.get("추출담보명", ""),
                    "보장금액": row.get("보장금액", ""),
                    "규칙추천": row.get("규칙추천", ""),
                    "규칙일치도": row.get("규칙일치도", 0.0),
                }
            )

        prompt = f"""
너는 보험 담보 매핑 AI다.

각 추출 담보를 목표 담보 LIST 중 하나로 매핑해라.
맞는 항목이 없으면 "매핑 제외"로 답해라.
회사담보명과 신정원담보명을 모두 참고해라.

[목표 담보 LIST]
{json.dumps(target_coverages, ensure_ascii=False)}

[AI 분석 대상]
{json.dumps(compact_items, ensure_ascii=False)}

반드시 JSON 객체만 출력:
{{
  "results": [
    {{
      "row_id": 0,
      "recommended_label": "목표 담보명 또는 매핑 제외",
      "confidence": 0.0,
      "reason": "짧은 근거"
    }}
  ]
}}
""".strip()

        print(f"[AI 일괄매핑] 요청 시작: {start + 1}~{start + len(chunk)} / {len(ai_targets)}")

        result = ask_ollama_json(
            prompt=prompt,
            model=model,
            temperature=0.0,
            timeout=90,
        )

        print(f"[AI 일괄매핑] 응답 완료: {type(result)}")

        if not isinstance(result, dict):
            continue

        results = result.get("results")
        if not isinstance(results, list):
            continue

        for item in results:
            if not isinstance(item, dict):
                continue

            try:
                row_id = int(item.get("row_id"))
            except Exception:
                continue

            label = item.get("recommended_label", "매핑 제외")

            if label not in target_coverages and label != "매핑 제외":
                label = "매핑 제외"

            try:
                confidence = float(item.get("confidence", 0.0))
            except Exception:
                confidence = 0.0

            all_output[row_id] = {
                "AI추천": label,
                "AI신뢰도": round(confidence * 100, 1),
                "AI사유": item.get("reason", ""),
            }

        print(f"[AI 일괄매핑] 누적 파싱: {len(all_output)}건")

    return all_output


def decide_final_mapping(row, ai_result=None):
    saved = row.get("저장소매핑")

    if saved:
        saved_status = clean_text(saved.get("status", "")) or "자동매핑"
        saved_label = clean_recommend_label(saved.get("target_label", ""))

        # 저장소에 이미 확인필요로 저장된 행은 자동매핑으로 승격하지 않는다.
        if saved_status == "확인필요":
            return {
                "상태": "확인필요",
                "추천위치": saved_label,
                "확정위치": saved_label,
                "AI추천": "",
                "AI신뢰도": 0.0,
                "AI사유": "저장소 확인필요 항목",
            }

        if saved_status == "매핑 제외":
            return {
                "상태": "매핑 제외",
                "추천위치": "매핑 제외",
                "확정위치": "매핑 제외",
                "AI추천": "",
                "AI신뢰도": 0.0,
                "AI사유": "저장소 매핑 제외 항목",
            }

        return {
            "상태": "자동매핑",
            "추천위치": saved_label,
            "확정위치": saved_label,
            "AI추천": "",
            "AI신뢰도": 0.0,
            "AI사유": "저장소 매핑 사용",
        }

    rule_label = clean_recommend_label(row.get("규칙추천", ""))
    rule_score = float(row.get("규칙일치도", 0.0))

    # 기존 코드의 핵심 문제: 30점 미만을 매핑 제외로 보냈음.
    # 수정 후: 추출된 담보는 검토표에 남기기 위해 확인필요로 보낸다.
    if rule_score < AI_ANALYZE_MIN_SCORE:
        return {
            "상태": "확인필요",
            "추천위치": "",
            "확정위치": "",
            "AI추천": "",
            "AI신뢰도": 0.0,
            "AI사유": "규칙일치도 30점 미만: 수동 확인 필요",
        }

    if rule_score >= AUTO_MATCH_SCORE and rule_label:
        return {
            "상태": "자동매핑",
            "추천위치": rule_label,
            "확정위치": rule_label,
            "AI추천": "",
            "AI신뢰도": 0.0,
            "AI사유": "규칙일치도 85점 이상",
        }

    if ai_result:
        ai_label_raw = clean_text(ai_result.get("AI추천", ""))
        ai_label = clean_recommend_label(ai_label_raw)
        ai_confidence = float(ai_result.get("AI신뢰도", 0.0))
        ai_reason = ai_result.get("AI사유", "")

        # AI가 매핑 제외라고 해도 자동 제외하지 않는다.
        # PDF 추출 결과를 사람이 검사할 수 있게 확인필요로 남긴다.
        if not ai_label:
            return {
                "상태": "확인필요",
                "추천위치": rule_label,
                "확정위치": "",
                "AI추천": ai_label_raw,
                "AI신뢰도": ai_confidence,
                "AI사유": ai_reason or "AI가 매핑 제외로 판단: 수동 확인 필요",
            }

        if ai_confidence >= AI_AUTO_CONFIDENCE * 100:
            status = "자동매핑"
            confirmed_label = ai_label
        else:
            status = "확인필요"
            confirmed_label = ""

        return {
            "상태": status,
            "추천위치": ai_label,
            "확정위치": confirmed_label,
            "AI추천": ai_label,
            "AI신뢰도": ai_confidence,
            "AI사유": ai_reason,
        }

    return {
        "상태": "확인필요",
        "추천위치": rule_label,
        "확정위치": "",
        "AI추천": "",
        "AI신뢰도": 0.0,
        "AI사유": "AI 미사용 또는 응답 실패: 수동 확인 필요",
    }


def make_mapping_candidates(parsed_data, target_coverages=None, use_ai=True, ai_model="qwen2.5:7b"):
    target_coverages = target_coverages or DEFAULT_TARGET_COVERAGES
    base_rows = normalize_extracted_rows(parsed_data)

    rule_rows = []
    ai_targets = []

    print(f"[매핑] 전체 추출담보: {len(base_rows)}건")

    saved_count = 0

    for row in base_rows:
        saved = find_saved_mapping(
            company=row.get("보험사", ""),
            product=row.get("상품명", ""),
            source_name=row.get("추출담보명", ""),
            company_coverage_name=row.get("회사담보명", ""),
            credit_coverage_name=row.get("신정원담보명", ""),
        )

        if saved:
            row["저장소매핑"] = saved
            row["규칙추천"] = saved.get("target_label", "")
            row["규칙일치도"] = 100.0
            saved_count += 1
            rule_rows.append(row)
            continue

        row["저장소매핑"] = None

        rule_label, rule_score = rule_based_recommend(row["매칭검토문구"], target_coverages)

        row["규칙추천"] = rule_label
        row["규칙일치도"] = rule_score

        rule_rows.append(row)

        if AI_ANALYZE_MIN_SCORE <= rule_score < AUTO_MATCH_SCORE:
            ai_targets.append(row)

    print(f"[매핑] 저장소 매핑: {saved_count}건")
    print(f"[매핑] AI 분석 대상: {len(ai_targets)}건")

    ai_results = {}

    if use_ai and ai_targets:
        ai_results = ai_batch_recommend(
            ai_targets=ai_targets,
            target_coverages=target_coverages,
            model=ai_model,
            chunk_size=10,
        )

    final_rows = []

    for row in rule_rows:
        final = decide_final_mapping(
            row=row,
            ai_result=ai_results.get(row["row_id"]),
        )

        final_rows.append(
            {
                "상태": final["상태"],
                "보험사": row.get("보험사", ""),
                "상품명": row.get("상품명", ""),
                "가입시기": row.get("가입시기", ""),
                "갱신주기": row.get("갱신주기", ""),
                "회사담보명": row.get("회사담보명", ""),
                "신정원담보명": row.get("신정원담보명", ""),
                "추출담보명": row.get("추출담보명", ""),
                "보장금액": row.get("보장금액", ""),
                "추천위치": final["추천위치"],
                "확정위치": final["확정위치"],
                "규칙추천": row.get("규칙추천", ""),
                "규칙일치도": row.get("규칙일치도", 0.0),
                "AI추천": final["AI추천"],
                "AI신뢰도": final["AI신뢰도"],
                "AI사유": final["AI사유"],
            }
        )

    status_counts = {}
    for row in final_rows:
        status = row.get("상태", "") or "미지정"
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"[매핑] 최종 결과: {len(final_rows)}건")
    print(f"[매핑] 상태별 결과: {status_counts}")

    return final_rows
