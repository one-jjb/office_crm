from pathlib import Path
from datetime import datetime

import streamlit as st

from utils.customer import get_customers
from tools.pdf_converter import convert_pdfs_to_excel


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_ROOT = BASE_DIR / "uploads" / "claim_analyze"
OUTPUT_ROOT = BASE_DIR / "outputs" / "claim_analyze"


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


def claim_analyze_page(user):
    st.subheader("PDF 변환")

    customers = get_customers(user)

    if not customers:
        st.info("먼저 고객을 등록해야 변환을 진행할 수 있습니다.")
        return

    if "selected_claim_customer_id" not in st.session_state:
        st.session_state.selected_claim_customer_id = None

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

    if st.session_state.selected_claim_customer_id in customer_ids:
        default_index = customer_ids.index(
            st.session_state.selected_claim_customer_id
        )

    selected_label = st.selectbox(
        "변환할 고객 선택",
        option_labels,
        index=default_index
    )

    selected_customer_id = customer_options[selected_label]
    st.session_state.selected_claim_customer_id = selected_customer_id

    if selected_customer_id is None:
        st.info("PDF를 변환할 고객을 선택하세요.")
        return

    selected_customer_name = selected_label.split(" / ")[0]

    st.divider()

    st.write("**심평원 PDF 3개 업로드**")
    st.caption("기본진료내역, 세부진료내역, 처방내역 PDF를 업로드하세요.")

    uploaded_files = st.file_uploader(
        "PDF 파일 업로드",
        type=["pdf"],
        accept_multiple_files=True
    )

    password = st.text_input(
        "PDF 비밀번호",
        type="password"
    )

    output_name = st.text_input(
        "결과 파일명",
        value=f"{safe_name(selected_customer_name)}_진료내역변환.xlsx"
    )

    run_convert = st.button(
        "PDF → Excel 변환 실행",
        use_container_width=True
    )

    if run_convert:
        if not uploaded_files:
            st.warning("PDF 파일을 업로드하세요.")
            return

        if len(uploaded_files) != 3:
            st.warning("심평원 PDF 3개를 업로드해야 합니다.")
            return

        if not password.strip():
            st.warning("PDF 비밀번호를 입력하세요.")
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

        saved_pdf_paths = []

        try:
            for uploaded_file in uploaded_files:
                saved_path = save_uploaded_file(
                    uploaded_file,
                    job_upload_dir
                )
                saved_pdf_paths.append(saved_path)

            with st.spinner("PDF를 엑셀로 변환 중입니다..."):
                result = convert_pdfs_to_excel(
                    pdf_paths=saved_pdf_paths,
                    password=password.strip(),
                    output_dir=job_output_dir,
                    output_filename=output_name.strip()
                )

            st.session_state.last_claim_convert_result = result

            if result.get("success"):
                st.success(result.get("message", "변환이 완료되었습니다."))
            else:
                st.error(result.get("message", "변환에 실패했습니다."))

            failed_files = result.get("failed_files") or []

            if failed_files:
                st.warning("일부 파일 처리 실패")
                for item in failed_files:
                    st.write(f"- {item}")

        except Exception as e:
            st.error(f"변환 중 오류가 발생했습니다: {e}")

    st.divider()

    result = st.session_state.get("last_claim_convert_result")

    if result and result.get("success"):
        output_path = Path(result["output_path"])

        if output_path.exists():
            st.write("**최근 변환 결과**")
            st.write(str(output_path))

            with open(output_path, "rb") as f:
                st.download_button(
                    label="변환된 엑셀 다운로드",
                    data=f,
                    file_name=output_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.warning("결과 파일 경로가 존재하지 않습니다.")