# C:\office_crm\tools\ollama_client.py

import json
from typing import Any, Dict, List, Optional

import requests


OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

DEFAULT_MODEL = "qwen2.5:7b"


def is_ollama_available(timeout: int = 3) -> bool:
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def get_ollama_models(timeout: int = 5) -> List[str]:
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        models = data.get("models", [])

        names = []
        for model in models:
            name = model.get("name")
            if name:
                names.append(name)

        return names

    except Exception:
        return []


def ask_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    temperature: float = 0.2,
    timeout: int = 60,
) -> str:
    if not system_prompt:
        system_prompt = (
            "너는 보험 보장분석 보조 AI다. "
            "제공된 데이터 안에서만 분석한다. "
            "확인되지 않은 내용은 단정하지 말고 '확인 필요'라고 표시한다. "
            "한국어로 간결하게 답변한다."
        )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "options": {
            "temperature": temperature,
            "num_predict": 800,
        },
        "stream": False,
    }

    try:
        response = requests.post(
            OLLAMA_CHAT_URL,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()

        data = response.json()
        return data.get("message", {}).get("content", "").strip()

    except requests.exceptions.ConnectionError:
        return (
            "Ollama 서버에 연결할 수 없습니다.\n\n"
            "확인 명령어:\n"
            "ollama --version\n"
            "ollama list\n"
            "ollama run qwen2.5:7b"
        )

    except requests.exceptions.Timeout:
        return (
            "Ollama 응답 시간이 초과되었습니다.\n\n"
            "가능한 원인:\n"
            "1. 모델이 너무 큼\n"
            "2. 첫 로딩 중임\n"
            "3. PC 메모리/RAM 부족\n"
            "4. qwen2.5:7b 모델이 아직 다운로드되지 않음\n\n"
            "CMD에서 먼저 실행해보세요:\n"
            "ollama run qwen2.5:7b"
        )

    except requests.exceptions.HTTPError as e:
        return f"Ollama HTTP 오류: {e}"

    except Exception as e:
        return f"Ollama 호출 오류: {e}"


def ask_ollama_json(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    temperature: float = 0.0,
    timeout: int = 60,
) -> Dict[str, Any]:
    json_system_prompt = (
        system_prompt
        or (
            "너는 보험 보장분석 데이터를 JSON으로 정리하는 AI다. "
            "반드시 JSON 객체만 출력한다. "
            "마크다운 코드블록은 쓰지 않는다."
        )
    )

    text = ask_ollama(
        prompt=prompt,
        model=model,
        system_prompt=json_system_prompt,
        temperature=temperature,
        timeout=timeout,
    )

    try:
        return json.loads(text)
    except Exception:
        return {
            "success": False,
            "raw_text": text,
        }


def build_coverage_analysis_prompt(parsed_data: Any) -> str:
    try:
        data_text = json.dumps(
            parsed_data,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    except Exception:
        data_text = str(parsed_data)

    return f"""
아래는 고객 보험 PDF에서 추출된 데이터입니다.

[추출 데이터]
{data_text}

다음 형식으로 짧게 정리해줘.

1. 전체 요약
2. 주요 보장 요약
3. 부족하거나 확인 필요한 항목
4. 상담용 코멘트

주의:
- 없는 항목을 없다고 단정하지 말고 '확인 필요'라고 표시
- 약관 확인이 필요한 내용은 '약관 확인 필요'라고 표시
- 답변은 너무 길게 하지 말 것
""".strip()


def analyze_coverage_with_ollama(
    parsed_data: Any,
    model: str = DEFAULT_MODEL,
) -> str:
    prompt = build_coverage_analysis_prompt(parsed_data)

    return ask_ollama(
        prompt=prompt,
        model=model,
        temperature=0.2,
        timeout=60,
    )


def recommend_mapping_with_ollama(
    source_name: str,
    master_labels: List[str],
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    prompt = f"""
추출 담보명을 MASTER_DATA 라벨 후보 중 어디에 매핑해야 할지 추천해줘.

[추출 담보명]
{source_name}

[MASTER_DATA 라벨 후보]
{json.dumps(master_labels, ensure_ascii=False, indent=2)}

JSON 형식으로만 답해줘.

{{
  "source_name": "{source_name}",
  "recommended_label": "추천 라벨 또는 확인 필요",
  "confidence": 0.0,
  "reason": "간단한 이유"
}}
""".strip()

    return ask_ollama_json(
        prompt=prompt,
        model=model,
        temperature=0.0,
        timeout=60,
    )