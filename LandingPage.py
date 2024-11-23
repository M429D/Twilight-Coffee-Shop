# landing_page.py
import streamlit as st

# Check the URL query parameters
payment_status = st.query_params.get("payment", [""])  # Get 'success' or 'fail'

# Determine payment status based on query parameters
if payment_status == "success":
    st.success("Thank you for your payment! Your order has been successfully processed.")
    payment_status_variable = "success"
elif payment_status == "fail":
    st.error("Payment failed. Please try again or contact support.")
    payment_status_variable = "fail"
else:
    st.warning("No payment status provided.")
    payment_status_variable = "unknown"

# Store the payment status in session state for access from other pages
st.session_state["payment_status"] = payment_status_variable
