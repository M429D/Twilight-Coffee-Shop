import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta

def admin_home():
    st.markdown("""<br>""", unsafe_allow_html=True)
    st.markdown("### 📊 Today's Performance Metrics")
    col1, col2, col3 = st.columns(3)

    # Get today's and yesterday's dates
    today_str = pd.Timestamp.now().strftime("%Y-%m-%d")
    yesterday_str = (pd.Timestamp.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Load all_users_order_history.csv
    orders_df = pd.read_csv("all_users_order_history.csv")

    # Filter for completed orders for today and yesterday
    orders_today = orders_df[
        (orders_df["Status"] == "Completed") &
        (orders_df["Time"].str.contains(today_str))
    ]
    orders_yesterday = orders_df[
        (orders_df["Status"] == "Completed") &
        (orders_df["Time"].str.contains(yesterday_str))
    ]

    # Calculate metrics for today and yesterday
    total_sales_today = orders_today["Price"].sum()
    total_sales_yesterday = orders_yesterday["Price"].sum() if not orders_yesterday.empty else 0

    orders_processed_today = len(orders_today)
    orders_processed_yesterday = len(orders_yesterday) if not orders_yesterday.empty else 0

    # Calculate unique order numbers for today and yesterday
    unique_orders_today = orders_today["Order Number"].nunique()
    unique_orders_yesterday = orders_yesterday["Order Number"].nunique() if not orders_yesterday.empty else 0

    # Calculate deltas with handling for missing yesterday's data
    if total_sales_yesterday > 0:
        sales_delta = ((total_sales_today - total_sales_yesterday) / total_sales_yesterday * 100)
    else:
        sales_delta = None  # No data for yesterday

    if unique_orders_yesterday > 0:
        unique_orders_delta = ((unique_orders_today - unique_orders_yesterday) / unique_orders_yesterday * 100)
    else:
        unique_orders_delta = None  # No data for yesterday

    # Load customer_feedback.json
    with open("customer_feedback.json", "r") as f:
        feedback_data = json.load(f)
    feedback_df = pd.DataFrame(feedback_data)

    # Filter for today's and yesterday's feedback
    feedback_today = feedback_df[feedback_df["date"].str.contains(today_str)]
    feedback_yesterday = feedback_df[feedback_df["date"].str.contains(yesterday_str)]

    # Calculate average feedback scores
    avg_feedback_today = feedback_today[["food_quality_rating", "service_rating", "uiux_rating"]].mean().mean()
    avg_feedback_yesterday = feedback_yesterday[["food_quality_rating", "service_rating", "uiux_rating"]].mean().mean() if not feedback_yesterday.empty else 0

    # Calculate feedback delta
    if avg_feedback_yesterday > 0:
        feedback_delta = ((avg_feedback_today - avg_feedback_yesterday) / avg_feedback_yesterday * 100)
    else:
        feedback_delta = None  # No data for yesterday

    # Display metrics with deltas
    col1, col2, col3 = st.columns(3)

    with col1:
        if sales_delta is not None:
            st.metric(
                label="Total Sales",
                value=f"RM {total_sales_today:,.2f}",
                delta=f"{sales_delta:.2f}%"
            )
        else:
            st.metric(
                label="Total Sales",
                value=f"RM {total_sales_today:,.2f}",
                delta="No data for comparison"
            )

    with col2:
        if unique_orders_delta is not None:
            st.metric(
                label="Unique Orders Processed",
                value=unique_orders_today,
                delta=f"{unique_orders_delta:.2f}%"
            )
        else:
            st.metric(
                label="Orders Completed",
                value=unique_orders_today,
                delta="No data for comparison"
            )

    with col3:
        if feedback_delta is not None:
            st.metric(
                label="Average Feedback Score",
                value=f"{avg_feedback_today:.2f}/5",
                delta=f"{feedback_delta:.2f}%"
            )
        else:
            st.metric(
                label="Average Feedback Score",
                value=f"{avg_feedback_today:.2f}/5",
                delta="No data for comparison"
            )

    st.markdown("---")

    # Snapshot of upcoming tasks or reminders
    st.markdown("### 📝 Daily Tasks")
    st.write(
        """
        - 📦 **Inventory Check**: Review stock levels by 5 PM.
        - 💬 **Team Meeting**: Discuss upcoming promotions at 3 PM.
        - 📊 **Weekly Report**: Review sales and analytics report by 8 PM.
        - 🚀 **Staff Schedule**: Finalize and communicate staff shifts for the next day.
        - 🆕 **Menu Update**: Discuss on adding new seasonal food & drinks to the menu.
        - 🔍 **Order Review**: Verify all completed orders and pending orders before closing at 10 PM.
        - 📦 **Supplier Follow-Up**: Confirm delivery schedules with suppliers for other essential items.
        - 🔧 **Maintenance Check**: Inspect equipment (coffee machines, refrigerators) for any issues by 8 PM.
        - 🧹 **End-of-Day Cleaning**: Ensure all areas (kitchen and customer seating) are cleaned before closing.
        """
    )

    st.markdown("---")

    st.markdown("### 💬 Customer Feedback")
    if not feedback_today.empty:
        st.dataframe(feedback_today.style.set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}]))
    else:
        st.write("No feedback received today.")

    st.markdown(
        """
        <br><br>
        <div style="text-align: center; font-size: 20px;">
            <strong><em>Powered by Twilight Coffee Shop Admin Dashboard</em></strong>
        </div>
        """,
        unsafe_allow_html=True
    )
