from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

from utils.page_common import require_login, render_sidebar
from tools.coverage_pdf_parser import parse_coverage_pdf
from tools.coverage_mapping_engine import (
    make_mapping_candidates,
    extract_coverages_from_parsed_data,
    extract_contracts_from_parsed_data,
)
from tools.coverage_mapping_store import (
    list_mapping_rules,
    upsert_mapping_rule_by_id,
    delete_mapping_rule,
    delete_mapping_rules,
    save_mapping_rule,
    save_confirmed_mappings,
)
from tools.coverage_target_store import (
    get_default_target_coverages,
    list_target_coverages,
    replace_target_coverages,
    upsert_target_coverage_by_id,
    add_target_coverage,
    delete_target_coverage,
)


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_ROOT = BASE_DIR / "uploads" / "mapping_store_admin"


st.set_page_config(
    page_title="매핑 저장소 관리",
    page_icon="🗂️",
    layout="wide",
)


PDF_MAPPING_COLUMNS = [
    "상태",
    "저장범위",
    "보험사",
    "상품명",
    "가입시기",
    "회사담보명",
    "신정원담보명",
    "추출담보명",
    "보장금액",
    "추천위치",
    "확정위치",
    "규칙추천",
    "규칙일치도",
    "AI추천",
    "AI신뢰도",
    "AI사유",
    "메모",
]


STORE_COLUMNS = [
    "선택",
    "ID",
    "상태",
    "저장범위",
    "보험사",
    "상품명",
    "가입시기",
    "회사담보명",
    "신정원담보명",
    "추출담보명",
    "보장금액",
    "매핑대상",
    "사용횟수",
    "수정일시",
    "마지막사용일시",
    "메모",
]


def is_admin_user(user):
    if not user:
        return False
    return str(user.get("role", "")).lower() == "admin"


def safe_name(value):
    text = str(value or "").strip()
    for ch in r'\/:*?"<>|':
        text = text.replace(ch, "_")
    return text or "unknown"


def save_uploaded_file(uploaded_file, save_dir):
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / safe_name(uploaded_file.name)

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return save_path


def display_only_columns(df, visible_cols):
    if df is None or df.empty:
        return df

    df = df.copy()

    for col in visible_cols:
        if col not in df.columns:
            df[col] = ""

    return df[visible_cols].copy()


def clean_text_value(value):
    """AgGrid / pandas 값의 NaN, None, 공백을 안전하게 빈 문자열로 정리합니다."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def first_non_empty(*values):
    """여러 후보 값 중 첫 번째 유효 문자열을 반환합니다."""
    for value in values:
        text = clean_text_value(value)
        if text:
            return text
    return ""


def normalize_status_value(value, target_value=""):
    """
    상태값 보정 규칙:
    - 자동매핑 / 확인필요 / 매핑 제외 외 값은 허용하지 않음
    - 상태가 비어 있으면 기본값은 확인필요
    - 매핑대상 자체가 '매핑 제외'이면 상태도 매핑 제외
    """
    target_text = clean_text_value(target_value)
    text = clean_text_value(value)

    if target_text == "매핑 제외":
        return "매핑 제외"

    if text in ["자동매핑", "확인필요", "매핑 제외"]:
        return text

    return "확인필요"


def normalize_scope_value(value):
    text = clean_text_value(value)
    if text in ["product", "company", "global"]:
        return text
    return "product"


def normalize_pdf_mapping_df(df):
    """
    PDF 매핑 후보 화면용 보정.
    이전 문제 방지:
    - 상태가 빈 값이면 확인필요로 표시
    - 추천위치가 비어 있으면 규칙추천/AI추천/mapped_category 계열 값을 후보로 채움
    - 확정위치가 비어 있어도 저장 전 추천위치로 보완 가능하게 구조 유지
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=PDF_MAPPING_COLUMNS)

    df = df.copy().reset_index(drop=True)

    for col in PDF_MAPPING_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    for idx, row in df.iterrows():
        suggested = first_non_empty(
            row.get("추천위치", ""),
            row.get("규칙추천", ""),
            row.get("AI추천", ""),
            row.get("mapped_category", ""),
            row.get("매핑대상", ""),
            row.get("target_label", ""),
        )

        confirmed = first_non_empty(
            row.get("확정위치", ""),
            row.get("매핑대상", ""),
            row.get("target_label", ""),
        )

        df.at[idx, "추천위치"] = suggested
        df.at[idx, "확정위치"] = confirmed
        df.at[idx, "저장범위"] = normalize_scope_value(row.get("저장범위", "product"))
        df.at[idx, "상태"] = normalize_status_value(row.get("상태", ""), first_non_empty(confirmed, suggested))

    return display_only_columns(df, PDF_MAPPING_COLUMNS)


def prepare_save_targets_for_store(df):
    """
    저장 직전 보정.
    - 자동매핑/확인필요 모두 저장소에 남도록 매핑대상 후보를 확정위치 우선, 추천위치 보조로 채움
    - 상태가 비어 있으면 확인필요로 살림
    - 매핑 제외만 저장 제외 대상으로 둠
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=PDF_MAPPING_COLUMNS)

    save_df = normalize_pdf_mapping_df(df)

    for idx, row in save_df.iterrows():
        target = first_non_empty(row.get("확정위치", ""), row.get("추천위치", ""))
        status = normalize_status_value(row.get("상태", ""), target)

        save_df.at[idx, "확정위치"] = target
        save_df.at[idx, "매핑대상"] = target
        save_df.at[idx, "target_label"] = target
        save_df.at[idx, "상태"] = status
        save_df.at[idx, "status"] = status
        save_df.at[idx, "저장범위"] = normalize_scope_value(row.get("저장범위", "product"))
        save_df.at[idx, "scope"] = save_df.at[idx, "저장범위"]

    return save_df


def normalize_store_display_df(df):
    """
    저장소 조회/수정 화면용 보정.
    - DB에서 status가 비어 있거나 누락되면 확인필요로 표시
    - target_label은 매핑대상으로 표시
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=STORE_COLUMNS)

    df = df.copy().reset_index(drop=True)

    for col in STORE_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    if "선택" in df.columns:
        df["선택"] = df["선택"].fillna(False).astype(bool)

    for idx, row in df.iterrows():
        target = first_non_empty(row.get("매핑대상", ""), row.get("확정위치", ""), row.get("target_label", ""))
        df.at[idx, "매핑대상"] = target
        df.at[idx, "상태"] = normalize_status_value(row.get("상태", ""), target)
        df.at[idx, "저장범위"] = normalize_scope_value(row.get("저장범위", "product"))

    return df[STORE_COLUMNS].copy()


def get_target_options():
    options = ["매핑 제외"] + get_default_target_coverages()
    deduped = []
    seen = set()

    for item in options:
        item = str(item or "").strip()
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)

    return deduped


def reset_pdf_mapping_state():
    for key in [
        "admin_mapping_pdf_path",
        "admin_mapping_parsed_data",
        "admin_mapping_df",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def to_pdf_mapping_display_df(df):
    return normalize_pdf_mapping_df(df)


def to_store_display_df(rules):
    if rules is None:
        return pd.DataFrame(columns=STORE_COLUMNS)

    if isinstance(rules, pd.DataFrame):
        if rules.empty:
            return pd.DataFrame(columns=STORE_COLUMNS)

        df = rules.copy().reset_index(drop=True)

        for col in STORE_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        return normalize_store_display_df(df)

    if not rules:
        return pd.DataFrame(columns=STORE_COLUMNS)

    df = pd.DataFrame(rules).reset_index(drop=True)

    rename_map = {
        "id": "ID",
        "scope": "저장범위",
        "company": "보험사",
        "product": "상품명",
        "contract_date": "가입시기",
        "company_coverage_name": "회사담보명",
        "credit_coverage_name": "신정원담보명",
        "source_name": "추출담보명",
        "amount": "보장금액",
        "target_label": "매핑대상",
        "status": "상태",
        "use_count": "사용횟수",
        "updated_at": "수정일시",
        "last_used_at": "마지막사용일시",
        "memo": "메모",
    }

    df = df.rename(columns=rename_map)

    if "선택" not in df.columns:
        df.insert(0, "선택", False)

    return normalize_store_display_df(df)


def from_store_display_row(row):
    target = first_non_empty(row.get("매핑대상", ""), row.get("확정위치", ""), row.get("target_label", ""))
    status = normalize_status_value(row.get("상태", row.get("status", "")), target)

    return {
        "id": row.get("ID", row.get("id", "")),
        "scope": normalize_scope_value(row.get("저장범위", row.get("scope", "product"))),
        "company": row.get("보험사", row.get("company", "")),
        "product": row.get("상품명", row.get("product", "")),
        "contract_date": row.get("가입시기", row.get("contract_date", "")),
        "company_coverage_name": row.get("회사담보명", row.get("company_coverage_name", "")),
        "credit_coverage_name": row.get("신정원담보명", row.get("credit_coverage_name", "")),
        "source_name": row.get("추출담보명", row.get("source_name", "")),
        "amount": row.get("보장금액", row.get("amount", "")),
        "target_label": target,
        "status": status,
        "memo": row.get("메모", row.get("memo", "")),
    }


def render_extract_summary(parsed_data):
    contracts = extract_contracts_from_parsed_data(parsed_data)
    coverages = extract_coverages_from_parsed_data(parsed_data)

    c1, c2 = st.columns(2)

    with c1:
        st.metric("계약 정보", f"{len(contracts)}건")

    with c2:
        st.metric("추출 담보", f"{len(coverages)}건")

    tab1, tab2, tab3 = st.tabs(["계약 정보", "추출 담보", "원본 데이터"])

    with tab1:
        if contracts:
            df = pd.DataFrame(contracts).reset_index(drop=True)
            visible_cols = [
                "no",
                "보험사",
                "상품명",
                "가입시기",
                "premium",
                "premium_number",
            ]
            st.dataframe(display_only_columns(df, visible_cols), width="stretch", hide_index=True)
        else:
            st.info("계약 정보 추출값이 없습니다.")

    with tab2:
        if coverages:
            rows = [
                item if isinstance(item, dict) else {"추출담보명": str(item)}
                for item in coverages
            ]

            df = pd.DataFrame(rows).reset_index(drop=True)
            visible_cols = [
                "page_no",
                "보험사",
                "상품명",
                "가입시기",
                "pay_type",
                "회사담보명",
                "신정원담보명",
                "담보명",
                "category",
                "보장금액",
                "amount_number",
                "mapped_category",
            ]
            st.dataframe(display_only_columns(df, visible_cols), width="stretch", hide_index=True)
        else:
            st.info("담보 추출값이 없습니다.")

    with tab3:
        with st.expander("원본 추출 데이터 보기"):
            st.write(parsed_data)


def render_pdf_mapping_grid(df, target_options, key):
    df = to_pdf_mapping_display_df(df)

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        editable=True,
        filter=True,
        sortable=True,
        resizable=True,
        wrapText=True,
        autoHeight=True,
    )

    for col in ["규칙일치도", "AI신뢰도"]:
        if col in df.columns:
            gb.configure_column(col, editable=False)

    gb.configure_column(
        "상태",
        editable=True,
        cellEditor="agRichSelectCellEditor",
        cellEditorParams={
            "values": ["자동매핑", "확인필요", "매핑 제외"],
            "allowTyping": True,
            "filterList": True,
            "searchType": "matchAny",
            "highlightMatch": True,
        },
    )

    gb.configure_column(
        "저장범위",
        editable=True,
        cellEditor="agRichSelectCellEditor",
        cellEditorParams={
            "values": ["product", "company", "global"],
            "allowTyping": True,
            "filterList": True,
            "searchType": "matchAny",
            "highlightMatch": True,
        },
    )

    gb.configure_column(
        "추천위치",
        editable=True,
        cellEditor="agRichSelectCellEditor",
        cellEditorParams={
            "values": target_options,
            "allowTyping": True,
            "filterList": True,
            "searchType": "matchAny",
            "highlightMatch": True,
        },
    )

    gb.configure_column(
        "확정위치",
        editable=True,
        header_name="확정위치",
        tooltipField="확정위치",
    )

    gb.configure_grid_options(
        stopEditingWhenCellsLoseFocus=True,
        singleClickEdit=True,
        suppressClickEdit=False,
        undoRedoCellEditing=True,
        undoRedoCellEditingLimit=20,
    )

    response = AgGrid(
        df,
        gridOptions=gb.build(),
        height=600,
        width="100%",
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        key=key,
    )

    return normalize_pdf_mapping_df(pd.DataFrame(response["data"]).reset_index(drop=True))


def render_store_grid(df, target_options, key):
    df = df.copy().reset_index(drop=True)

    for col in STORE_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[STORE_COLUMNS].copy()

    if "선택" in df.columns:
        df["선택"] = df["선택"].fillna(False).astype(bool)

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        editable=True,
        filter=True,
        sortable=True,
        resizable=True,
        wrapText=True,
        autoHeight=True,
    )

    gb.configure_column("선택", editable=True, pinned="left", width=80)
    gb.configure_column("ID", editable=False, pinned="left", width=90)

    for col in ["사용횟수", "수정일시", "마지막사용일시"]:
        if col in df.columns:
            gb.configure_column(col, editable=False)

    gb.configure_column(
        "상태",
        editable=True,
        cellEditor="agRichSelectCellEditor",
        cellEditorParams={
            "values": ["자동매핑", "확인필요", "매핑 제외"],
            "allowTyping": True,
            "filterList": True,
            "searchType": "matchAny",
            "highlightMatch": True,
        },
    )

    gb.configure_column(
        "저장범위",
        editable=True,
        cellEditor="agRichSelectCellEditor",
        cellEditorParams={
            "values": ["product", "company", "global"],
            "allowTyping": True,
            "filterList": True,
            "searchType": "matchAny",
            "highlightMatch": True,
        },
    )

    gb.configure_column(
        "매핑대상",
        editable=True,
        cellEditor="agRichSelectCellEditor",
        cellEditorParams={
            "values": target_options,
            "allowTyping": True,
            "filterList": True,
            "searchType": "matchAny",
            "highlightMatch": True,
        },
    )

    gb.configure_grid_options(
        stopEditingWhenCellsLoseFocus=True,
        singleClickEdit=True,
        suppressClickEdit=False,
        undoRedoCellEditing=True,
        undoRedoCellEditingLimit=20,
    )

    response = AgGrid(
        df,
        gridOptions=gb.build(),
        height=620,
        width="100%",
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        key=key,
    )

    return normalize_store_display_df(pd.DataFrame(response["data"]).reset_index(drop=True))


def render_pdf_mapping_register():
    st.subheader("PDF 기반 매핑 저장소 등록")
    st.caption("여기는 AI/규칙 추천을 검토하는 구간이라 `추천위치`와 `확정위치`를 나눠 둡니다.")

    uploaded_pdf = st.file_uploader(
        "매핑 저장소 등록용 PDF 업로드",
        type=["pdf"],
        key="admin_mapping_pdf_uploader",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("PDF 추출 실행", type="primary", width="stretch", key="admin_pdf_extract_btn"):
            if not uploaded_pdf:
                st.warning("PDF 파일을 업로드하세요.")
                return

            job_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_dir = UPLOAD_ROOT / job_time
            pdf_path = save_uploaded_file(uploaded_pdf, save_dir)

            with st.spinner("PDF에서 담보 정보를 추출 중입니다..."):
                parsed_data = parse_coverage_pdf(pdf_path)

            st.session_state.admin_mapping_pdf_path = str(pdf_path)
            st.session_state.admin_mapping_parsed_data = parsed_data
            st.session_state.admin_mapping_df = None

            st.success("PDF 추출이 완료되었습니다.")
            st.rerun()

    with col2:
        if st.button("작업 초기화", width="stretch", key="admin_pdf_reset_btn"):
            reset_pdf_mapping_state()
            st.rerun()

    parsed_data = st.session_state.get("admin_mapping_parsed_data")

    if not parsed_data:
        return

    st.divider()
    render_extract_summary(parsed_data)

    st.divider()
    st.markdown("#### 매핑 후보 생성 설정")

    default_targets = get_default_target_coverages()

    target_text = st.text_area(
        "목표 담보 LIST",
        value="\n".join(default_targets),
        height=230,
        key="admin_pdf_target_text",
    )

    target_list = [line.strip() for line in target_text.splitlines() if line.strip()]

    use_ai = st.checkbox(
        "Ollama AI 사용",
        value=True,
        help="규칙일치도 30~84점 구간만 AI가 검토합니다.",
        key="admin_pdf_use_ai",
    )

    ai_model = st.selectbox(
        "AI 모델",
        ["qwen2.5:3b", "qwen2.5:7b", "llama3.1:8b"],
        index=0,
        key="admin_pdf_ai_model",
    )

    if st.button("매핑 후보 생성", type="primary", width="stretch", key="admin_pdf_make_mapping_btn"):
        with st.spinner("저장소/규칙/AI 기준으로 매핑 후보 생성 중입니다..."):
            mapping_rows = make_mapping_candidates(
                parsed_data=parsed_data,
                target_coverages=target_list,
                use_ai=use_ai,
                ai_model=ai_model,
            )

        mapping_df = pd.DataFrame(mapping_rows).reset_index(drop=True)
        mapping_df["저장범위"] = "product"
        mapping_df["메모"] = ""

        st.session_state.admin_mapping_df = to_pdf_mapping_display_df(mapping_df)
        st.success("매핑 후보 생성이 완료되었습니다.")
        st.rerun()

    mapping_df = st.session_state.get("admin_mapping_df")

    if mapping_df is None or mapping_df.empty:
        return

    st.divider()
    st.markdown("#### 매핑값 확정 / 수정")
    st.info("확정위치는 직접 입력 가능합니다. 복수 매핑은 | 또는 , 로 구분하세요.")

    target_options = ["매핑 제외"] + target_list

    edited_df = render_pdf_mapping_grid(
        mapping_df,
        target_options=target_options,
        key="admin_pdf_mapping_aggrid",
    )

    st.session_state.admin_mapping_df = edited_df.reset_index(drop=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("자동매핑", f"{len(edited_df[edited_df['상태'] == '자동매핑'])}건")

    with c2:
        st.metric("확인필요", f"{len(edited_df[edited_df['상태'] == '확인필요'])}건")

    with c3:
        st.metric("매핑 제외", f"{len(edited_df[edited_df['상태'] == '매핑 제외'])}건")

    save_targets = prepare_save_targets_for_store(edited_df)

    st.divider()
    st.markdown("#### 저장 대상 미리보기")

    preview_cols = [
        "상태",
        "보험사",
        "상품명",
        "회사담보명",
        "신정원담보명",
        "추출담보명",
        "추천위치",
        "확정위치",
    ]

    preview_df = save_targets.copy()

    for col in preview_cols:
        if col not in preview_df.columns:
            preview_df[col] = ""

    st.dataframe(preview_df[preview_cols], width="stretch", hide_index=True)

    st.caption(
        "※ 자동매핑/확인필요 상태는 저장 대상입니다. "
        "확정위치가 비어 있으면 추천위치를 매핑대상으로 보완하고, 매핑 제외 상태만 저장되지 않습니다."
    )

    if st.button("확정 매핑 저장소에 저장", type="primary", width="stretch", key="admin_pdf_save_mapping_btn"):
        save_result = save_confirmed_mappings(
            save_targets,
            default_scope="product",
        )

        st.success(
            f"저장 완료: {save_result['saved']}건 저장 / "
            f"{save_result['skipped']}건 제외"
        )

        latest_rules = list_mapping_rules(limit=20)

        if latest_rules:
            latest_df = pd.DataFrame(latest_rules).reset_index(drop=True)

            visible_cols = [
                "id",
                "company",
                "product",
                "company_coverage_name",
                "credit_coverage_name",
                "source_name",
                "target_label",
                "status",
                "updated_at",
            ]

            for col in visible_cols:
                if col not in latest_df.columns:
                    latest_df[col] = ""

            st.write("최근 저장된 저장소 데이터")
            st.dataframe(latest_df[visible_cols], width="stretch", hide_index=True)

        st.rerun()


def render_store_editor():
    st.subheader("저장소 매핑 규칙 조회 / 수정")
    st.caption("저장소는 이미 확정된 룰을 관리하는 구간이라 `추천위치` 없이 `매핑대상`만 사용합니다.")

    rules = list_mapping_rules(limit=5000)

    if not rules:
        st.info("저장된 매핑 규칙이 없습니다.")
        return

    store_df = to_store_display_df(rules)
    target_options = get_target_options()

    existing_targets = [
        str(value).strip()
        for value in store_df.get("매핑대상", [])
        if str(value).strip()
    ]

    for value in existing_targets:
        if value not in target_options:
            target_options.append(value)

    edited_df = render_store_grid(
        store_df,
        target_options=target_options,
        key="store_rules_aggrid",
    )

    metric_c1, metric_c2, metric_c3, metric_c4 = st.columns(4)
    with metric_c1:
        st.metric("전체", f"{len(edited_df)}건")
    with metric_c2:
        st.metric("자동매핑", f"{len(edited_df[edited_df['상태'] == '자동매핑'])}건")
    with metric_c3:
        st.metric("확인필요", f"{len(edited_df[edited_df['상태'] == '확인필요'])}건")
    with metric_c4:
        st.metric("매핑 제외", f"{len(edited_df[edited_df['상태'] == '매핑 제외'])}건")

    selected_ids = []

    if "선택" in edited_df.columns and "ID" in edited_df.columns:
        selected_df = edited_df[edited_df["선택"] == True]
        selected_ids = selected_df["ID"].dropna().tolist()

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("표 수정사항 전체 저장", type="primary", width="stretch", key="store_grid_save_btn"):
            saved = 0

            for _, row in edited_df.iterrows():
                row_dict = from_store_display_row(row.to_dict())
                ok = upsert_mapping_rule_by_id(row_dict)

                if ok:
                    saved += 1

            st.success(f"{saved}건 저장 완료")
            st.rerun()

    with c2:
        if st.button("선택 규칙 삭제", width="stretch", key="store_selected_delete_btn"):
            if not selected_ids:
                st.warning("삭제할 규칙을 체크하세요.")
            else:
                deleted_count = delete_mapping_rules(selected_ids)
                st.success(f"{deleted_count}건 삭제 완료")
                st.rerun()

    with c3:
        delete_id = st.number_input("ID 직접 삭제", min_value=0, step=1, key="store_delete_id")

        if st.button("ID 삭제", width="stretch", key="store_delete_btn"):
            if delete_id <= 0:
                st.warning("삭제할 ID를 입력하세요.")
            else:
                ok = delete_mapping_rule(delete_id)

                if ok:
                    st.success(f"ID {delete_id} 삭제 완료")
                    st.rerun()
                else:
                    st.error("삭제 실패 또는 존재하지 않는 ID입니다.")


def render_target_coverage_manager():
    st.subheader("목표 담보 LIST 관리")

    current_labels = get_default_target_coverages()

    target_text = st.text_area(
        "기본 목표 담보 LIST",
        value="\n".join(current_labels),
        height=360,
        key="target_manager_text",
    )

    if st.button("기본 목표 담보 LIST 저장", type="primary", width="stretch", key="target_manager_save_btn"):
        labels = [line.strip() for line in target_text.splitlines() if line.strip()]

        result = replace_target_coverages(labels)
        st.success(result["message"])
        st.rerun()

    st.divider()
    st.markdown("#### 상세 관리")

    rows = list_target_coverages(include_inactive=True)

    if rows:
        edited_df = st.data_editor(
            pd.DataFrame(rows).reset_index(drop=True),
            width="stretch",
            hide_index=True,
            num_rows="fixed",
            key="target_manager_editor",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "target_label": st.column_config.TextColumn("목표 담보명", required=True),
                "sort_order": st.column_config.NumberColumn("정렬순서"),
                "is_active": st.column_config.CheckboxColumn("사용"),
                "memo": st.column_config.TextColumn("메모"),
            },
        )

        if st.button("상세 수정사항 저장", width="stretch", key="target_manager_detail_save_btn"):
            saved = 0

            for _, row in edited_df.iterrows():
                if upsert_target_coverage_by_id(row):
                    saved += 1

            st.success(f"{saved}건 저장 완료")
            st.rerun()
    else:
        st.info("등록된 목표 담보가 없습니다.")

    st.divider()
    st.markdown("#### 목표 담보 추가 / 삭제")

    col1, col2 = st.columns(2)

    with col1:
        new_label = st.text_input("추가할 목표 담보명", key="target_add_label")
        new_order = st.number_input("정렬순서", min_value=0, step=1, key="target_add_order")
        new_memo = st.text_input("메모", key="target_add_memo")

        if st.button("목표 담보 추가", width="stretch", key="target_add_btn"):
            ok = add_target_coverage(
                target_label=new_label,
                sort_order=new_order,
                memo=new_memo,
            )

            if ok:
                st.success("추가 완료")
                st.rerun()
            else:
                st.error("추가 실패: 목표 담보명을 입력하세요.")

    with col2:
        delete_id = st.number_input("삭제할 목표 담보 ID", min_value=0, step=1, key="target_delete_id")

        if st.button("목표 담보 삭제", width="stretch", key="target_delete_btn"):
            if delete_id <= 0:
                st.warning("삭제할 ID를 입력하세요.")
            else:
                ok = delete_target_coverage(delete_id)

                if ok:
                    st.success(f"ID {delete_id} 삭제 완료")
                    st.rerun()
                else:
                    st.error("삭제 실패 또는 존재하지 않는 ID입니다.")


def render_manual_register():
    st.subheader("신규 매핑 직접 등록")
    st.caption("복수 매핑은 매핑 대상에 `상해입원비 | 질병입원비`처럼 입력하세요.")

    scope = st.radio(
        "적용범위",
        ["product", "company", "global"],
        format_func=lambda x: {
            "global": "전체 공통",
            "company": "보험사 기준",
            "product": "보험사+상품 기준",
        }.get(x, x),
        horizontal=True,
        key="manual_scope",
    )

    company = st.text_input("보험사", key="manual_company")
    product = st.text_input("상품명", key="manual_product")
    contract_date = st.text_input("가입시기", key="manual_contract_date")
    source_name = st.text_input("추출담보명", key="manual_source_name")
    company_coverage_name = st.text_input("회사담보명", key="manual_company_coverage_name")
    credit_coverage_name = st.text_input("신정원담보명", key="manual_credit_coverage_name")
    amount = st.text_input("보장금액", key="manual_amount")

    target_label = st.text_input(
        "매핑 대상",
        key="manual_target_label",
        help="복수 매핑은 | 또는 , 로 구분하세요.",
    )

    status = st.selectbox(
        "상태",
        ["자동매핑", "확인필요", "매핑 제외"],
        key="manual_status",
    )

    memo = st.text_area("메모", key="manual_memo")

    if st.button("신규 매핑 저장", type="primary", width="stretch", key="manual_save_btn"):
        ok = save_mapping_rule(
            source_name=source_name,
            company_coverage_name=company_coverage_name,
            credit_coverage_name=credit_coverage_name,
            target_label=target_label,
            status=status,
            company=company,
            product=product,
            contract_date=contract_date,
            amount=amount,
            scope=scope,
            memo=memo,
        )

        if ok:
            st.success("신규 매핑 저장 완료")
            st.rerun()
        else:
            st.error("저장 실패: 추출담보명, 회사담보명, 신정원담보명 중 하나와 매핑 대상은 필수입니다.")


def main():
    require_login()
    render_sidebar()

    user = st.session_state.get("user")

    if not is_admin_user(user):
        st.error("관리자만 접근할 수 있는 페이지입니다.")
        st.stop()

    st.title("🗂️ 매핑 저장소 관리")
    st.caption("PDF 기반 등록, 저장소 조회/수정, 목표 담보 LIST, 신규 매핑 등록을 관리합니다.")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "PDF로 매핑 등록",
            "저장소 조회/수정",
            "목표 담보 LIST 관리",
            "신규 직접 등록",
        ]
    )

    with tab1:
        render_pdf_mapping_register()

    with tab2:
        render_store_editor()

    with tab3:
        render_target_coverage_manager()

    with tab4:
        render_manual_register()


if __name__ == "__main__":
    main()