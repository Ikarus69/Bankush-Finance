import streamlit as st
import pandas as pd
from models.client import Client
from dashboard.layout import load_css
import requests
from streamlit_lottie import st_lottie


class Dashboard:

    def render(self):
        load_css()
        st.title("Borrower Credit Evaluation Dashboard")

        # =========================
        # SESSION STATE INIT
        # =========================
        if "clients" not in st.session_state:
            st.session_state.clients = []

        if "debt_inputs" not in st.session_state:
            st.session_state.debt_inputs = [{"name": "", "amount": 0}]

        if "form_submitted" not in st.session_state:
            st.session_state.form_submitted = False

        # --- Lottie animation ---
        lottie_ani = self.load_lottie_url(
            "https://assets2.lottiefiles.com/packages/lf20_touohxv0.json"
        )
        if lottie_ani:
            st_lottie(lottie_ani, speed=1, height=150)

        # =========================
        # SIDEBAR NAVIGATION
        # =========================
        st.sidebar.markdown("## Bankush Finance")
        sections = [
            "Borrower Financial Overview",
            "Loan Repayment Likelihood",
            "Key Decision Factors",
            "Eligibility & Recommendations",
            "Loan Decision Summary"
        ]

        if "selected_dashboard" not in st.session_state:
            st.session_state.selected_dashboard = sections[0]

        for sec in sections:
            selected = st.session_state.selected_dashboard == sec
            color = "#16a34a" if selected else "#065f46"

            if st.sidebar.button(sec, key=sec):
                st.session_state.selected_dashboard = sec

            st.markdown(f"""
                <style>
                div.stButton > button[key="{sec}"] {{
                    background-color: {color};
                    color: white;
                    font-weight: bold;
                    border-radius: 10px;
                    padding: 14px;
                    margin-bottom: 10px;
                }}
                </style>
            """, unsafe_allow_html=True)

        option = st.session_state.selected_dashboard

        # =========================
        # ADD BORROWER FORM
        # =========================
        if not st.session_state.form_submitted:
            st.subheader("Add New Borrower")

            name = st.text_input("Borrower Name", "")
            income = st.number_input("Monthly Income (PHP)", 0, 500000, 1000)

            st.markdown("### Existing Debts")
            total_debt = 0
            for i, debt in enumerate(st.session_state.debt_inputs):
                col1, col2 = st.columns(2)
                debt["name"] = col1.text_input(
                    f"Debt Name #{i+1}", debt["name"], key=f"debt_name_{i}"
                )
                debt["amount"] = col2.number_input(
                    "Amount (PHP)", 0, 1000000, debt["amount"], key=f"debt_amount_{i}"
                )
                total_debt += debt["amount"]

            st.markdown(f"**Total Existing Debt:** `PHP {total_debt:,}`")

            col_add, col_submit = st.columns(2)
            if col_add.button("➕ Add Another Debt"):
                st.session_state.debt_inputs.append({"name": "", "amount": 0})
                st.rerun()

            if col_submit.button("Add Borrower"):
                if not name.strip():
                    st.warning("Please enter borrower name")
                else:
                    client_id = len(st.session_state.clients) + 1
                    client = Client(client_id, income, total_debt, name=name)
                    st.session_state.clients.append(client.to_dict())
                    st.session_state.debt_inputs = [{"name": "", "amount": 0}]
                    st.session_state.form_submitted = True
                    st.success("Borrower added successfully!")

        if not st.session_state.clients:
            st.info("Add borrowers to begin evaluation.")
            return

        df = pd.DataFrame(st.session_state.clients)
        borrower = df.iloc[-1]

        # =========================
        # 1️⃣ BORROWER FINANCIAL OVERVIEW
        # =========================
        if option == "Borrower Financial Overview":
            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Borrower Name", borrower["Name"])
            col2.metric("Monthly Income", f"PHP {borrower['Income (PHP)']:,}")
            col3.metric("Existing Debt", f"PHP {borrower['Debts (PHP)']:,}")
            col4.metric(
                "Debt-to-Income Ratio",
                f"{borrower['Debts (PHP)'] / max(borrower['Income (PHP)'], 1):.2f}"
            )

        # =========================
        # 2️⃣ LOAN REPAYMENT LIKELIHOOD
        # =========================
        elif option == "Loan Repayment Likelihood":
            likelihood = (
                "High" if borrower["Risk Level"] == "Low"
                else "Moderate" if borrower["Risk Level"] == "Medium"
                else "Low"
            )
            st.progress(min(borrower["Score"] / 3, 1.0))
            st.markdown(f"**Likelihood to Repay:** `{likelihood}`")

        # =========================
        # 3️⃣ KEY DECISION FACTORS
        # =========================
        elif option == "Key Decision Factors":
            st.markdown(f"""
            - **Income Stability:** {"Strong" if borrower['Income (PHP)'] > 2000 else "Weak"}
            - **Debt-to-Income Ratio:** {"Healthy" if borrower['Debts (PHP)']/max(borrower['Income (PHP)'],1) < 0.4 else "Risky"}
            """)

        # =========================
        # 4️⃣ ELIGIBILITY & RECOMMENDATIONS
        # =========================
        elif option == "Eligibility & Recommendations":
            if borrower["Eligibility"] == "Eligible":
                st.success("Eligible for loan approval")
            else:
                st.warning("Conditionally eligible or declined")

            st.markdown("### Recommendations")
            if borrower["Debts (PHP)"] > borrower["Income (PHP)"] * 0.4:
                st.write("- Reduce outstanding debt")
            if borrower["Income (PHP)"] < 2000:
                st.write("- Provide additional income documentation")

        # =========================
        # 5️⃣ LOAN DECISION SUMMARY
        # =========================
        elif option == "Loan Decision Summary":
            st.markdown(f"""
            **Decision:** `{borrower['Eligibility']}`  
            **Approved Amount:** `PHP 8,000`  
            **Suggested Term:** `12 months`  
            **Borrowing Risk Score:** `{borrower['Score']}`  
            """)

    @staticmethod
    def load_lottie_url(url: str):
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
