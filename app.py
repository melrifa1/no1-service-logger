# quick_log.py
import streamlit as st
import datetime, time
from supabase import create_client
import pytz
UTC_TZ = pytz.utc
st.set_page_config(page_title="Quick Service Log", layout="centered")
sb = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["service_key"])

st.title("Quick Service Log")

# -------------------------
# LOGIN UI (only show when not logged in)
# -------------------------
if "quick_user" not in st.session_state:
    pin = st.text_input(
        "Enter PIN",
        type="password",
        key="pin_input"
    )

    if st.button("Login"):
        user = (
            sb.table("users")
            .select("id, username, pin, service_percentage, is_active")
            .eq("pin", pin)   # make sure DB stores 4-char PINs
            .eq("is_active", True)
            .limit(1)
            .execute()
            .data
        )

        if not user:
            st.error("Invalid PIN or account disabled.")
        else:
            st.session_state["quick_user"] = user[0]
            st.rerun()

# -------------------------
# SERVICE FORM (only show when logged in)
# -------------------------
if "quick_user" in st.session_state:
    user = st.session_state["quick_user"]
    st.success(f"Welcome {user['username']} 👋")

    # Logout button
    if st.button("Logout"):
        st.session_state.pop("quick_user", None)
        st.rerun()

    with st.form("quick_log_form", clear_on_submit=True):
        amount_str = st.text_input("Service Amount")
        tip_str = st.text_input("Tip")
        # payment_type = st.selectbox("Payment Type", ["Credit", "Cash"])
        payment_type = st.radio(
            "Payment Type",
            ["Credit", "Cash"],
            index=0,  # Default to "Credit"
            horizontal=True
        )
        submitted = st.form_submit_button("Save & Logout")

    if submitted:
        # Convert to floats
        try:
            amount = float(amount_str) if amount_str.strip() else None
        except Exception:
            st.error("Service Amount must be a number.")
            amount = None

        try:
            tip = float(tip_str) if tip_str.strip() else 0.0
        except Exception:
            st.error("Tip must be a number.")
            tip = 0.0

        if amount is None:
            st.error("Amount is required and must be > 0.")
        else:
            sb.table("service_logs").insert({
                "user_id": user["id"],
                "served_at": datetime.datetime.now(UTC_TZ).isoformat(),
                "amount_cents": amount,
                "tip_cents": tip,
                "payment_type": payment_type
            }).execute()

            st.success("✅ Service logged. Logging out...")
            time.sleep(1)

            # log out
            st.session_state.pop("quick_user", None)
            st.rerun()
