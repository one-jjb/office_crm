from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from utils.customer import get_customers
from tools.excel_analyzer import analyze_excel_file


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_ROOT = BASE_DIR / "uploads" / "excel_analyze"
OUTPUT_ROOT = BASE_DIR / "outputs" / "excel_analyze"


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


def parse_letters(value):
    text = str(value or "").strip()

    if not text:
        return []

    return [
        item.strip().upper()
        for item in text.split(",")
        if item.strip()
    ]


def excel_analyze_page(user):
    st.subheader("변환 엑셀 정리 / 분석")

    customers = get_customers(user)

    if not customers:
        st.info("먼저 고객을 등록해야 분석을 진행할 수 있습니다.")
        return

    if "selected_excel_customer_id" not in st.session_state:
        st.session_state.selected_excel_customer_id = None

    customer_options = {"(선택)": None}

    for customer in customers:
        label = (
            f"{customer.get('name') or '이름없음'} / "
            f"{customer.get('phone') or '연락처 없음'}"
        )

        customer_options[label] = customer["id"]

    option_labels = list(customer_options.keys())
    customer_ids = list(customer_options.values())

    default_index = 0

    if st.session_state.selected_excel_customer_id in customer_ids:
        default_index = customer_ids.index(
            st.session_state.selected_excel_customer_id
        )

    selected_label = st.selectbox(
        "분석할 고객 선택",
        option_labels,
        index=default_index
    )

    selected_customer_id = customer_options[selected_label]
    st.session_state.selected_excel_customer_id = selected_customer_id

    if selected_customer_id is None:
        st.info("엑셀을 분석할 고객을 선택하세요.")
        return

    selected_customer_name = selected_label.split(" / ")[0]

    st.divider()

    uploaded_excel = st.file_uploader(
        "변환된 엑셀 파일 업로드",
        type=["xlsx", "xlsm", "xls"]
    )

    st.divider()

    st.write("**분석 조건 설정**")

    col1, col2, col3 = st.columns(3)

    with col1:
        years = st.number_input(
            "최근 몇 년 기준",
            min_value=1,
            max_value=30,
            value=5,
            step=1
        )

        cond2_count = st.number_input(
            "조건2: 상병코드 N회 이상",
            min_value=1,
            max_value=100,
            value=7,
            step=1
        )

        include_condition3 = st.checkbox(
            "조건3: 입원 포함",
            value=True
        )

    with col2:
        cond4_prefix_letters = st.text_input(
            "조건4: 코드 첫 글자",
            value="F,C,D,E,G,I,J",
            help="쉼표로 구분하세요. 예: F,C,D,E,G,I,J"
        )

        cond4_second_letters = st.text_input(
            "조건4: 코드 두 번째 글자",
            value="F,M,C,D,E,G,I,J",
            help="쉼표로 구분하세요. 예: F,M,C,D,E,G,I,J"
        )

    with col3:
        cond5_cost = st.number_input(
            "조건5: 총진료비 N원 이상",
            min_value=0,
            value=150000,
            step=10000
        )

        cond6_days = st.number_input(
            "조건6: 총투약일수 N일 이상",
            min_value=0,
            value=30,
            step=1
        )

        cond7_total_days = st.number_input(
            "조건7: 약품명별 총투약일수 합산 N일 이상",
            min_value=0,
            value=90,
            step=1
        )

    output_name = st.text_input(
        "결과 파일명",
        value=f"{safe_name(selected_customer_name)}_진료내역_분석파일.xlsx"
    )

    run_analyze = st.button(
        "엑셀 분석 실행",
        use_container_width=True
    )

    if run_analyze:
        if not uploaded_excel:
            st.warning("분석할 엑셀 파일을 업로드하세요.")
            return

        job_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        job_upload_dir = (
            UPLOAD_ROOT
            / f"customer_{selected_customer_id}"
            / job_time
        )

        job_output_dir = (
            OUTPUT_ROOT
            / f"customer_{selected_customer_id}"
            / job_time
        )

        try:
            saved_excel_path = save_uploaded_file(
                uploaded_excel,
                job_upload_dir
            )

            with st.spinner("엑셀 분석 중입니다..."):
                result = analyze_excel_file(
                    input_excel_path=saved_excel_path,
                    output_dir=job_output_dir,
                    years=int(years),
                    cond2_count=int(cond2_count),
                    include_condition3=include_condition3,
                    cond4_prefix_letters=parse_letters(cond4_prefix_letters),
                    cond4_second_letters=parse_letters(cond4_second_letters),
                    cond5_cost=int(cond5_cost),
                    cond6_days=int(cond6_days),
                    cond7_total_days=int(cond7_total_days),
                    output_filename=output_name.strip()
                )

            st.session_state.last_excel_analyze_result = result

            if result.get("success"):
                st.success(result.get("message", "분석이 완료되었습니다."))
            else:
                st.error(result.get("message", "분석에 실패했습니다."))

        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")

    st.divider()

    result = st.session_state.get("last_excel_analyze_result")

    if result:
        summary = result.get("summary") or []

        if summary:
            st.write("**최근 분석 요약**")
            st.dataframe(
                pd.DataFrame(summary),
                use_container_width=True,
                hide_index=True
            )

        if result.get("success"):
            output_path = Path(result["output_path"])

            if output_path.exists():
                st.write("**최근 분석 결과 파일**")
                st.write(str(output_path))

                with open(output_path, "rb") as f:
                    st.download_button(
                        label="분석 엑셀 다운로드",
                        data=f,
                        file_name=output_path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                st.warning("결과 파일 경로가 존재하지 않습니다.")