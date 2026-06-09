import streamlit as st


def inject_global_css():

    st.markdown("""
    <style>

    /* ======================================================
       기본
    ====================================================== */

    #MainMenu{
        visibility:hidden;
    }

    footer{
        visibility:hidden;
    }

    header{
        visibility:hidden;
    }

    [data-testid="stSidebar"]{
        background:#0F172A;
        border-right:1px solid rgba(255,255,255,0.06);
    }

    .block-container{
        padding-top:2rem;
        padding-bottom:2rem;
    }

    .stApp{
        background:
            linear-gradient(
                135deg,
                #0f172a,
                #111827,
                #1e293b
            );

        color:white;
    }

    /* ======================================================
       타이틀
    ====================================================== */

    .page-title{

        font-size:42px;

        font-weight:800;

        color:white;

        letter-spacing:-1px;

        margin-bottom:10px;
    }

    .page-sub{

        color:#94A3B8;

        font-size:16px;

        margin-bottom:32px;
    }

    /* ======================================================
       카드
    ====================================================== */

    .crm-card{

        background:rgba(255,255,255,0.05);

        border:1px solid rgba(255,255,255,0.08);

        border-radius:24px;

        padding:24px;

        backdrop-filter:blur(18px);

        box-shadow:
            0 10px 40px rgba(0,0,0,0.25);

        margin-bottom:20px;
    }

    /* ======================================================
       KPI 카드
    ====================================================== */

    .metric-card{

        background:
            linear-gradient(
                135deg,
                rgba(91,140,255,0.18),
                rgba(124,92,255,0.10)
            );

        border:1px solid rgba(255,255,255,0.08);

        border-radius:24px;

        padding:24px;

        backdrop-filter:blur(18px);
    }

    .metric-label{

        color:#CBD5E1;

        font-size:14px;

        margin-bottom:10px;
    }

    .metric-value{

        color:white;

        font-size:38px;

        font-weight:800;
    }

    /* ======================================================
       버튼
    ====================================================== */

    .stButton > button{

        border:none;

        border-radius:16px;

        background:
            linear-gradient(
                135deg,
                #5B8CFF,
                #7C5CFF
            );

        color:white;

        font-weight:600;
    }

    /* ======================================================
       input
    ====================================================== */

    .stTextInput > div > div > input{

        background:rgba(255,255,255,0.06);

        border:1px solid rgba(255,255,255,0.08);

        border-radius:14px;

        color:white;
    }

    /* ======================================================
       dataframe
    ====================================================== */

    [data-testid="stDataFrame"]{

        border-radius:20px;

        overflow:hidden;

        border:1px solid rgba(255,255,255,0.08);
    }

    /* ======================================================
       sidebar nav
    ====================================================== */

    section[data-testid="stSidebar"] *{

        color:white !important;
    }

    </style>
    """, unsafe_allow_html=True)