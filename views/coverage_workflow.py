# C:\office_crm\views\coverage_workflow.py

from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

from utils.customer import get_customers
from tools.coverage_pdf_parser import parse_coverage_pdf
from tools.coverage_mapping_engine import (
    make_mapping_candidates,
    extract_contracts_from_parsed_data,
    extract_coverages_from_parsed_data,
)
from tools.coverage_template_engine import generate_coverage_report_from_mapping
from tools.coverage_mapping_store import (
    save_confirmed_mappings,
    list_mapping_rules,
    split_mapping_labels,
)
from tools.coverage_target_store import get_default_target_coverages
from views.coverage_excel_preview import render_excel_preview


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_ROOT = BASE_DIR / "uploads" / "coverage_workflow"
OUTPUT_ROOT = BASE_DIR / "outputs" / "coverage_workflow"
TEMPLATE_DIR = BASE_DIR / "templates"


MAPPING_COLUMNS = [
    "ID",
    "상태",
    "저장범위",
    "보험사",
    "상품명",
    "가입시기",
    "갱신주기",
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


def get_template_files():
    if not TEMPLATE_DIR.exists():
        TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        return []

    return list(TEMPLATE_DIR.glob("*.xlsx"))


def display_only_columns(df, visible_cols):
    if df is None or df.empty:
        return df

    df = df.copy()

    for col in visible_cols:
        if col not in df.columns:
            df[col] = ""

    return df[visible_cols].copy()


def to_mapping_display_df(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=MAPPING_COLUMNS)

    df = df.copy().reset_index(drop=True)

    if "ID" not in df.columns:
        df["ID"] = ""

    if "저장범위" not in df.columns:
        df["저장범위"] = "product"

    if "메모" not in df.columns:
        df["메모"] = ""

    return display_only_columns(df, MAPPING_COLUMNS)


def expand_multi_mapping_rows(df):
    if df is None or df.empty:
        return df

    expanded_rows = []

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        target_value = row_dict.get("확정위치", "")

        labels = split_mapping_labels(target_value)

        if not labels:
            expanded_rows.append(row_dict)
            continue

        for label in labels:
            new_row = row_dict.copy()
            new_row["확정위치"] = label
            expanded_rows.append(new_row)

    return pd.DataFrame(expanded_rows).reset_index(drop=True)


def init_state():
    defaults = {
        "coverage_step": 1,
        "coverage_uploaded_pdf_path": None,
        "coverage_parsed_data": None,
        "coverage_mapping_df": None,
        "coverage_target_list": get_default_target_coverages(),
        "coverage_selected_template": None,
        "coverage_result": None,
        "coverage_customer": None,
        "coverage_remodel_type": "리모델링 전",
        "coverage_use_ai_mapping": True,
        "coverage_ai_model": "qwen2.5:3b",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_step(step):
    st.session_state.coverage_step = step


def render_step_bar():
    current = st.session_state.coverage_step
    cols = st.columns(6)

    steps = [
        (1, "PDF 업로드"),
        (2, "추출 확인"),
        (3, "작업 설정"),
        (4, "AI/매핑 검토"),
        (5, "결과 생성"),
        (6, "출력"),
    ]

    for col, (num, title) in zip(cols, steps):
        with col:
            if current == num:
                st.button(f"✅ {num}. {title}", width="stretch", disabled=True)
            else:
                st.button(
                    f"{num}. {title}",
                    width="stretch",
                    on_click=go_step,
                    args=(num,),
                )


def select_customer(user):
    customers = get_customers(user)

    if not customers:
        st.info("먼저 고객을 등록해야 합니다.")
        return None

    options = {"(선택)": None}

    for customer in customers:
        label = (
            f"{customer.get('name') or '이름없음'} / "
            f"{customer.get('phone') or '연락처 없음'}"
        )
        options[label] = customer["id"]

    selected = st.selectbox("고객 선택", list(options.keys()))
    customer_id = options[selected]

    if not customer_id:
        return None

    return {
        "id": customer_id,
        "label": selected,
        "name": selected.split(" / ")[0],
    }


def render_contract_summary(parsed_data):
    contracts = extract_contracts_from_parsed_data(parsed_data)

    if not contracts:
        st.info("계약 정보 추출값이 없습니다.")
        return

    rows = [item if isinstance(item, dict) else {"내용": str(item)} for item in contracts]
    df = pd.DataFrame(rows).reset_index(drop=True)

    visible_cols = [
        "no",
        "보험사",
        "상품명",
        "가입시기",
        "premium",
        "premium_number",
    ]

    df = display_only_columns(df, visible_cols)
    st.dataframe(df, width="stretch", hide_index=True)


def render_coverage_summary(parsed_data):
    coverages = extract_coverages_from_parsed_data(parsed_data)

    if not coverages:
        st.info("담보 정보 추출값이 없습니다.")
        return

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

    df = display_only_columns(df, visible_cols)
    st.dataframe(df, width="stretch", hide_index=True)


def render_extraction_dashboard(parsed_data):
    st.markdown("#### 추출 요약")

    contracts = extract_contracts_from_parsed_data(parsed_data)
    coverages = extract_coverages_from_parsed_data(parsed_data)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("계약 정보", f"{len(contracts)}건")

    with c2:
        st.metric("담보 정보", f"{len(coverages)}건")

    with c3:
        st.metric("처리 상태", "추출 완료")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["계약 정보", "담보 정보", "원본 추출값"])

    with tab1:
        render_contract_summary(parsed_data)

    with tab2:
        render_coverage_summary(parsed_data)

    with tab3:
        with st.expander("원본 추출 데이터 보기"):
            st.write(parsed_data)


def render_unified_mapping_grid(df, target_options, key):
    df = to_mapping_display_df(df)

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        editable=True,
        filter=True,
        sortable=True,
        resizable=True,
        wrapText=True,
        autoHeight=True,
    )

    readonly_cols = [
        "ID",
        "규칙일치도",
        "AI신뢰도",
    ]

    for col in readonly_cols:
        if col in df.columns:
            gb.configure_column(col, editable=False)

    if "ID" in df.columns:
        gb.configure_column("ID", pinned="left", width=90)

    if "상태" in df.columns:
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

    if "저장범위" in df.columns:
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

    if "추천위치" in df.columns:
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

    if "확정위치" in df.columns:
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

    return pd.DataFrame(response["data"]).reset_index(drop=True)


def step_1_upload(user):
    st.subheader("1단계 · 분석할 PDF 업로드")

    customer = select_customer(user)

    if not customer:
        st.info("고객을 선택하세요.")
        return

    uploaded_pdf = st.file_uploader(
        "보험 증권 / 가입설계서 / 보장내역 PDF 업로드",
        type=["pdf"],
    )

    if st.button("PDF 저장 후 추출 시작", type="primary", width="stretch"):
        if not uploaded_pdf:
            st.warning("PDF 파일을 업로드하세요.")
            return

        job_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = UPLOAD_ROOT / f"customer_{customer['id']}" / job_time
        pdf_path = save_uploaded_file(uploaded_pdf, save_dir)

        with st.spinner("PDF에서 보험사, 가입시기, 담보, 보장금액 등을 추출 중입니다..."):
            parsed_data = parse_coverage_pdf(pdf_path)

        st.session_state.coverage_uploaded_pdf_path = str(pdf_path)
        st.session_state.coverage_parsed_data = parsed_data
        st.session_state.coverage_customer = customer
        st.session_state.coverage_result = None
        st.session_state.coverage_mapping_df = None
        st.session_state.coverage_step = 2

        st.success("PDF 추출이 완료되었습니다.")
        st.rerun()


def step_2_extracted_review():
    st.subheader("2단계 · 추출 결과 확인")

    parsed_data = st.session_state.get("coverage_parsed_data")

    if not parsed_data:
        st.warning("추출된 데이터가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    render_extraction_dashboard(parsed_data)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("이전 단계", width="stretch"):
            go_step(1)
            st.rerun()

    with col2:
        if st.button("작업 설정으로 이동", type="primary", width="stretch"):
            go_step(3)
            st.rerun()


def step_3_work_setting():
    st.subheader("3단계 · 작업 전 입력 구간 설정")

    templates = get_template_files()

    if templates:
        template_names = [t.name for t in templates]
        selected_name = st.selectbox("사용할 출력 서식 선택", template_names)
        selected_template = TEMPLATE_DIR / selected_name
        st.session_state.coverage_selected_template = str(selected_template)
    else:
        st.warning("templates 폴더에 xlsx 템플릿 파일이 없습니다.")
        st.code(str(TEMPLATE_DIR), language="text")

    st.markdown("#### 찾아와야 하는 담보 LIST")

    if st.button("관리자 기본 목표 담보 LIST 다시 불러오기", width="stretch"):
        st.session_state.coverage_target_list = get_default_target_coverages()
        st.rerun()

    target_text = st.text_area(
        "한 줄에 하나씩 입력",
        value="\n".join(st.session_state.coverage_target_list),
        height=260,
    )

    target_list = [line.strip() for line in target_text.splitlines() if line.strip()]
    st.session_state.coverage_target_list = target_list

    remodel_type = st.radio(
        "입력 구간 선택",
        ["리모델링 전", "리모델링 후"],
        index=0 if st.session_state.coverage_remodel_type == "리모델링 전" else 1,
        horizontal=True,
    )
    st.session_state.coverage_remodel_type = remodel_type

    st.markdown("#### AI 매핑 설정")

    use_ai = st.checkbox(
        "Ollama AI가 추천위치 판단에 관여",
        value=st.session_state.coverage_use_ai_mapping,
    )
    st.session_state.coverage_use_ai_mapping = use_ai

    ai_model_options = ["qwen2.5:3b", "qwen2.5:7b", "llama3.1:8b"]

    current_model = st.session_state.coverage_ai_model
    current_index = ai_model_options.index(current_model) if current_model in ai_model_options else 0

    ai_model = st.selectbox("AI 모델", ai_model_options, index=current_index)
    st.session_state.coverage_ai_model = ai_model

    if use_ai:
        st.info(
            "규칙일치도 85점 이상은 자동매핑, 30점 미만은 매핑 제외, "
            "30~84점만 AI가 검토합니다."
        )

    st.caption("복수 매핑은 확정위치에 `상해입원비 | 질병입원비` 또는 `상해입원비, 질병입원비`처럼 입력하면 됩니다.")

    with st.expander("최근 저장된 매핑 규칙 보기"):
        rules = list_mapping_rules(limit=100)

        if rules:
            df = pd.DataFrame(rules).reset_index(drop=True)
            visible_cols = [
                "id",
                "scope",
                "company",
                "product",
                "contract_date",
                "company_coverage_name",
                "credit_coverage_name",
                "source_name",
                "amount",
                "target_label",
                "status",
                "use_count",
                "updated_at",
                "last_used_at",
                "memo",
            ]
            df = display_only_columns(df, visible_cols)
            st.dataframe(df, width="stretch", hide_index=True)
        else:
            st.info("저장된 매핑 규칙이 없습니다.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("이전 단계", width="stretch"):
            go_step(2)
            st.rerun()

    with col2:
        if st.button("AI 매핑 후보 생성", type="primary", width="stretch"):
            parsed_data = st.session_state.coverage_parsed_data

            with st.spinner("저장소/규칙/AI 기준으로 매핑 후보를 생성 중입니다..."):
                mapping_rows = make_mapping_candidates(
                    parsed_data=parsed_data,
                    target_coverages=target_list,
                    use_ai=use_ai,
                    ai_model=ai_model,
                )

            mapping_df = pd.DataFrame(mapping_rows).reset_index(drop=True)
            mapping_df["ID"] = ""
            mapping_df["저장범위"] = "product"
            mapping_df["메모"] = ""

            mapping_df = to_mapping_display_df(mapping_df)

            st.session_state.coverage_mapping_df = mapping_df
            st.session_state.coverage_result = None
            go_step(4)
            st.rerun()


def step_4_mapping_review():
    st.subheader("4단계 · AI / 매핑 검토")

    mapping_df = st.session_state.get("coverage_mapping_df")

    if mapping_df is None or mapping_df.empty:
        st.warning("매핑 후보가 없습니다. 작업 설정 단계에서 매핑 후보를 생성하세요.")
        return

    mapping_df = to_mapping_display_df(mapping_df)

    st.caption(
        "저장소 → 규칙 → AI 순서로 추천됩니다. "
        "회사담보명과 신정원담보명을 확인한 뒤 확정위치를 수정하세요."
    )

    st.info("관리자 매핑 저장소와 동일한 방식입니다. 확정위치는 직접 입력 가능하고, 복수 매핑은 | 또는 , 로 구분합니다.")

    target_options = ["매핑 제외"] + st.session_state.coverage_target_list

    edited_df = render_unified_mapping_grid(
        mapping_df,
        target_options=target_options,
        key="coverage_mapping_aggrid",
    )

    st.session_state.coverage_mapping_df = edited_df.reset_index(drop=True)

    auto_count = len(edited_df[edited_df["상태"] == "자동매핑"])
    check_count = len(edited_df[edited_df["상태"] == "확인필요"])
    exclude_count = len(edited_df[edited_df["상태"] == "매핑 제외"])

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("자동매핑", f"{auto_count}건")

    with c2:
        st.metric("확인필요", f"{check_count}건")

    with c3:
        st.metric("매핑 제외", f"{exclude_count}건")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("작업 설정으로 돌아가기", width="stretch"):
            go_step(3)
            st.rerun()

    with col2:
        if st.button("매핑 확정 후 결과 생성 단계로 이동", type="primary", width="stretch"):
            go_step(5)
            st.rerun()


def step_5_generate_result():
    st.subheader("5단계 · 정리된 내용 생성")

    mapping_df = st.session_state.get("coverage_mapping_df")
    template_path = st.session_state.get("coverage_selected_template")
    customer = st.session_state.get("coverage_customer") or {}
    remodel_type = st.session_state.get("coverage_remodel_type", "리모델링 전")

    if mapping_df is None or mapping_df.empty:
        st.warning("확정된 매핑 데이터가 없습니다.")
        return

    if not template_path:
        st.warning("선택된 템플릿이 없습니다.")
        return

    mapping_df = to_mapping_display_df(mapping_df)

    confirmed_df = mapping_df[mapping_df["상태"] != "매핑 제외"].copy().reset_index(drop=True)
    expanded_confirmed_df = expand_multi_mapping_rows(confirmed_df)

    visible_cols = [
        "상태",
        "보험사",
        "상품명",
        "가입시기",
        "회사담보명",
        "신정원담보명",
        "추출담보명",
        "보장금액",
        "확정위치",
        "AI사유",
        "메모",
    ]
    confirmed_df_view = display_only_columns(expanded_confirmed_df, visible_cols)

    st.markdown("#### 최종 입력 대상")
    st.dataframe(confirmed_df_view, width="stretch", hide_index=True)

    st.markdown("#### 확정 매핑 저장")

    if st.button("확정 매핑을 저장소에 저장", width="stretch"):
        save_result = save_confirmed_mappings(
            confirmed_df,
            default_scope="product",
        )

        st.success(
            f"매핑 저장 완료: {save_result['saved']}건 저장 / "
            f"{save_result['skipped']}건 제외"
        )

    output_filename = st.text_input(
        "출력 파일명",
        value=f"{safe_name(customer.get('name', '고객'))}_보장분석표.xlsx",
    )

    if st.button("보장분석표 생성 실행", type="primary", width="stretch"):
        job_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = OUTPUT_ROOT / f"customer_{customer.get('id', 'unknown')}" / job_time

        with st.spinner("확정된 매핑값을 템플릿에 입력 중입니다..."):
            result = generate_coverage_report_from_mapping(
                template_path=template_path,
                mapping_df=expanded_confirmed_df,
                output_dir=output_dir,
                output_filename=output_filename,
                remodel_type=remodel_type,
            )

        st.session_state.coverage_result = result
        st.success("보장분석표 생성이 완료되었습니다.")

        if result.get("unmatched"):
            st.warning("일부 항목은 템플릿에서 입력 위치를 찾지 못했습니다.")
            st.dataframe(
                pd.DataFrame(result["unmatched"]).reset_index(drop=True),
                width="stretch",
                hide_index=True,
            )

    result = st.session_state.get("coverage_result")

    if result and result.get("written"):
        st.markdown("#### 입력 완료 내역")
        st.dataframe(
            pd.DataFrame(result["written"]).reset_index(drop=True),
            width="stretch",
            hide_index=True,
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("매핑 검토로 돌아가기", width="stretch"):
            go_step(4)
            st.rerun()

    with col2:
        if st.button("출력 단계로 이동", type="primary", width="stretch"):
            go_step(6)
            st.rerun()


def step_6_output():
    st.subheader("6단계 · 출력")

    result = st.session_state.get("coverage_result")

    if not result:
        st.warning("생성된 결과가 없습니다. 먼저 5단계에서 보장분석표를 생성하세요.")
        return

    output_path = Path(result["output_path"])

    if not output_path.exists():
        st.error("결과 파일을 찾을 수 없습니다.")
        st.code(str(output_path), language="text")
        return

    render_excel_preview(output_path)

    st.divider()

    with open(output_path, "rb") as f:
        st.download_button(
            label="엑셀 다운로드",
            data=f,
            file_name=output_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )

    st.code(str(output_path), language="text")

    if st.button("처음부터 다시 시작", width="stretch"):
        for key in [
            "coverage_uploaded_pdf_path",
            "coverage_parsed_data",
            "coverage_mapping_df",
            "coverage_selected_template",
            "coverage_result",
        ]:
            st.session_state[key] = None

        st.session_state.coverage_target_list = get_default_target_coverages()
        st.session_state.coverage_step = 1
        st.rerun()


def coverage_workflow_page(user):
    init_state()

    st.title("📊 보장분석표 생성")
    st.caption("PDF 업로드 → 추출 확인 → 작업 구간 설정 → AI/매핑 검토 → 결과 생성 → 출력")

    render_step_bar()
    st.divider()

    step = st.session_state.coverage_step

    if step == 1:
        step_1_upload(user)
    elif step == 2:
        step_2_extracted_review()
    elif step == 3:
        step_3_work_setting()
    elif step == 4:
        step_4_mapping_review()
    elif step == 5:
        step_5_generate_result()
    elif step == 6:
        step_6_output()