import streamlit as st
import pandas as pd
from models.client import Client
from dashboard.layout import load_css
import requests
from streamlit_lottie import st_lottie

class Dashboard:

    def render(self):
        load_css()
        st.set_page_config(page_title="Borrower Credit Evaluation Dashboard", layout="wide")
        st.markdown(
            """
            <style>
            /* Main page background */
            .css-18e3th9 {
                background-color: #f8f9fa;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

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

        # =========================
        # SIDEBAR NAVIGATION
        # =========================
        st.sidebar.markdown("## Bankush Finance")

        # Sidebar CSS
        st.markdown(
            """
            <style>
            /* Sidebar background */
            [data-testid="stSidebar"] {
                background-color: #1e1e1e;
                color: white;
            }

            /* Sidebar title */
            [data-testid="stSidebar"] .css-1d391kg {
                color: white;
                font-weight: bold;
            }

            /* Sidebar buttons base */
            div.stButton > button {
                background-color: #333333;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                padding: 14px;
                margin-bottom: 10px;
                transition: all 0.2s;
            }

            /* Sidebar button hover */
            div.stButton > button:hover {
                background-color: #00ff00;
                color: #1e1e1e;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        sections = [
            "Borrower Overview",
            "Debts Overview",
            "Loan Summary",
            "Recommendations"
        ]

        if "selected_dashboard" not in st.session_state:
            st.session_state.selected_dashboard = sections[0]

        for sec in sections:
            selected = st.session_state.selected_dashboard == sec
            btn_color = "#00ff00" if selected else "#333333"
            text_color = "#1e1e1e" if selected else "white"

            if st.sidebar.button(sec, key=sec):
                st.session_state.selected_dashboard = sec

            # Apply inline CSS to specific button
            st.markdown(f"""
                <style>
                div.stButton > button[key="{sec}"] {{
                    background-color: {btn_color};
                    color: {text_color};
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
            loan_amount = st.number_input("Requested Loan Amount (PHP)", 0, 1000000, 10000)

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

            col_add, col_submit = st.columns(2)
            if col_add.button("➕ Add Another Debt"):
                st.session_state.debt_inputs.append({"name": "", "amount": 0})
                st.rerun()

            st.markdown(f"**Total Existing Debt:** `PHP {total_debt:,}`")

            if col_submit.button("Add Borrower"):
                if not name.strip():
                    st.warning("Please enter borrower name")
                else:
                    client_id = len(st.session_state.clients) + 1
                    debt_details = [{"name": d.get("name", "").strip() or "Unnamed Debt", "amount": d.get("amount", 0)} for d in st.session_state.debt_inputs]
                    client = Client(
                        client_id,
                        income,
                        total_debt,
                        loan_amount=loan_amount,
                        name=name,
                        debt_details=debt_details
                    )
                    st.session_state.clients.append(client.to_dict())
                    st.session_state.debt_inputs = [{"name": "", "amount": 0}]
                    st.session_state.form_submitted = True
                    st.success("Borrower added successfully!")

        if not st.session_state.clients:
            st.info("Add a borrower to begin evaluation.")
            return

        # =========================
        # SHOW BORROWER DASHBOARD
        # =========================
        borrower = st.session_state.clients[-1]

        # -------------------------
        # Borrower Overview
        # -------------------------
        if option == "Borrower Overview":
            st.markdown("### Borrower Financial Overview")

            col1, col2, col3, col4, col5 = st.columns(5)
            dti_color = "#16a34a" if borrower['DTI'] < 0.4 else "#dc2626"
            eligibility_color = "#16a34a" if borrower['Eligibility'] == "Eligible" else "#f59e0b"

            metrics = {
                "Name": {"value": borrower["Name"], "color": "#065f46"},
                "Monthly Income": {"value": f"PHP {borrower['Income (PHP)']:,}", "color": "#065f46"},
                "Existing Debt": {"value": f"PHP {borrower['Debts (PHP)']:,}", "color": "#065f46"},
                "Debt-to-Income Ratio": {"value": f"{borrower['DTI']:.2f}", "color": dti_color},
                "Requested Loan": {"value": f"PHP {borrower['Loan Amount']:,}", "color": "#065f46"}
            }

            for idx, (title, info) in enumerate(metrics.items()):
                with [col1, col2, col3, col4, col5][idx]:
                    st.markdown(f"""
                        <div style="
                            background-color:#ffffff;
                            padding:20px;
                            border-radius:12px;
                            text-align:center;
                            box-shadow:0 4px 8px rgba(0,0,0,0.1);
                        ">
                            <div style="font-weight:bold; font-size:18px; color:#065f46;">{title}</div>
                            <div style="font-size:24px; margin-top:5px; color:{info['color']};">{info['value']}</div>
                        </div>
                    """, unsafe_allow_html=True)

            # -------------------------
            # Decision Factors
            # -------------------------
            st.markdown("### Decision Factors")
            col1, col2 = st.columns(2)
            with col1:
                income_stability = "Strong" if borrower['Income (PHP)'] >= 2000 else "Weak"
                dti_status = "Healthy" if borrower['DTI'] < 0.4 else "Risky"
                st.markdown(f"- **Income Stability:** {income_stability}")
                st.markdown(f"- **Debt-to-Income Ratio:** {dti_status}")
            with col2:
                st.markdown(f"- **Eligibility:** <span style='color:{eligibility_color}; font-weight:bold'>{borrower['Eligibility']}</span>", unsafe_allow_html=True)
                st.markdown(f"- **Risk Level:** {borrower['Risk Level']}")

            # -------------------------
            # Debt Breakdown Chart
            # -------------------------
            if borrower.get("Debt Details"):
                st.markdown("### Debt Breakdown")
                debt_names = [d.get('name', 'Unnamed Debt') for d in borrower["Debt Details"]]
                debt_amounts = [d.get('amount', 0) for d in borrower["Debt Details"]]
                df_debt = pd.DataFrame({"Debt": debt_names, "Amount": debt_amounts})
                st.bar_chart(df_debt.set_index("Debt"))

        # -------------------------
        # Debts Overview
        # -------------------------
        elif option == "Debts Overview":
            st.markdown("### Borrower Debts")
            if borrower.get("Debt Details"):
                for debt in borrower["Debt Details"]:
                    debt_name = debt.get('name', '').strip() or "Unnamed Debt"
                    debt_amount = debt.get('amount', 0)
                    st.markdown(f"""
                        <div style="
                            background-color:#ffffff;
                            padding:15px;
                            border-radius:10px;
                            margin-bottom:10px;
                            box-shadow:0 3px 6px rgba(0,0,0,0.1);
                        ">
                            <strong>Debt Name:</strong> {debt_name} <br>
                            <strong>Amount:</strong> PHP {debt_amount:,}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No debts added yet.")

        # -------------------------
        # Recommendations
        # -------------------------
        elif option == "Recommendations":
            st.markdown("### Recommendations")
            recommendations = []

            if borrower['DTI'] < 0.4:
                recommendations.append({"text": "✅ Keep your debt-to-income ratio below 40% to maintain financial health", "type": "good"})
            else:
                recommendations.append({"text": "⚠️ Reduce outstanding debt to lower your debt-to-income ratio", "type": "warning"})

            if borrower['Income (PHP)'] >= 2000:
                recommendations.append({"text": "💵 Your income is stable. Keep monitoring your monthly expenses", "type": "good"})
            else:
                recommendations.append({"text": "⚠️ Consider providing additional income documentation or increasing income sources", "type": "warning"})

            if borrower['Debts (PHP)'] > borrower['Income (PHP)'] * 0.4:
                recommendations.append({"text": "⚠️ Consider lowering loan request or paying off some debts", "type": "warning"})
            else:
                recommendations.append({"text": "👍 Your debt level is manageable. Keep it that way", "type": "good"})

            for rec in recommendations:
                color = "#16a34a" if rec["type"] == "good" else "#f59e0b"
                st.markdown(f"""
                    <div style="
                        background-color:{color}33; 
                        padding:15px; 
                        border-left:6px solid {color}; 
                        border-radius:8px; 
                        margin-bottom:10px;
                        box-shadow:0 3px 6px rgba(0,0,0,0.1);
                        font-size:16px;
                    ">
                        {rec['text']}
                    </div>
                """, unsafe_allow_html=True)

        # -------------------------
        # Loan Summary (Professional Look)
        # -------------------------
        elif option == "Loan Summary":
            eligibility_color = (
                "#16a34a" if borrower['Eligibility'] == "Eligible" 
                else "#f59e0b" if borrower['Eligibility'] == "Conditionally Eligible" 
                else "#dc2626"
            )
            st.markdown(f"""
                <div style="
                    background-color:#ffffff;
                    padding:25px;
                    border-radius:15px;
                    box-shadow:0 4px 10px rgba(0,0,0,0.15);
                ">
                    <h3 style="color:{eligibility_color}; margin-bottom:15px;">
                        Loan Eligibility: {borrower['Eligibility']}
                    </h3>
                    <p style="font-size:16px; margin:5px 0;"><strong>Requested Loan Amount:</strong> PHP {borrower['Loan Amount']:,}</p>
                    <p style="font-size:16px; margin:5px 0;"><strong>Total Existing Debt:</strong> PHP {borrower['Debts (PHP)']:,}</p>
                    <p style="font-size:16px; margin:5px 0;"><strong>Debt-to-Income Ratio:</strong> {borrower['DTI']:.2f}</p>
                    <p style="font-size:16px; margin:5px 0;"><strong>Suggested Term:</strong> 12 months</p>
                    <p style="font-size:16px; margin:5px 0;"><strong>Borrowing Risk Score:</strong> {borrower['Score']}</p>
                </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def load_lottie_url(url: str):
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
