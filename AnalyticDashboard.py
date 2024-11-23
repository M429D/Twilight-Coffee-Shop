import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

def create_kpi_card(title, value, color):
    """Function to create a KPI card using Altair."""
    return alt.Chart(pd.DataFrame({'value': [value]})).mark_bar(color=color).encode(
        x=alt.X('value:Q', title=title, axis=alt.Axis(labels=False)),
        y=alt.Y('value:Q', title=''),
        tooltip=[alt.Tooltip('value:Q', title=title)]
    ).properties(
        width=100,
        height=50
    )

def analytics_dashboard():
    # Main Heading
    st.markdown(
        """
        <h1 style="text-align: center;">Analytics Dashboard</h1>
        <br>
        """,
        unsafe_allow_html=True
    )

    # Subheading for KPI
    st.markdown("<h2 style='text-align: left; color: orange;'>Today's KPI Dashboard</h2>", unsafe_allow_html=True)

    # Load the order history from the existing Excel file
    try:
        df = pd.read_csv('all_users_order_history.csv')
    except FileNotFoundError:
        st.error("Excel file not found. Please check the file path.")
        return
    except Exception as e:
        st.error(f"An error occurred while loading the Excel file: {str(e)}")
        return

    # Convert 'Time' column to datetime
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce')

    # Filter for today's date
    today = datetime.now().date()
    today_orders = df[df['Time'].dt.date == today]

    # Check if there are any orders for today
    if today_orders.empty:
        st.write("No orders found for today.")
        return
    
    # Store original data for metrics and charts
    original_today_orders = today_orders.copy()

    # KPI Calculations
    total_revenue = original_today_orders[original_today_orders['Status'] == 'Received']['Price'].sum()
    total_orders = today_orders['Order Number'].nunique()
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    received_orders = today_orders[today_orders['Status'] == 'Received']
    total_items_sold = received_orders['Quantity'].sum()

    # Create KPI cards for Total Revenue, Total Orders, Average Order Value, and Total Items Sold
    total_revenue_card = create_kpi_card("Total Revenue", total_revenue, "green")
    total_orders_card = create_kpi_card("Total Orders", total_orders, "blue")
    average_order_value_card = create_kpi_card("Avg Order Value", average_order_value, "orange")
    total_items_sold_card = create_kpi_card("Total Items Sold", total_items_sold, "purple")

    # Display the KPI dashboard
    st.markdown("<div class='subheading'>KPI Dashboard</div>", unsafe_allow_html=True)

    # Display KPI metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kpi_chart = alt.hconcat(total_revenue_card)
        st.altair_chart(kpi_chart, use_container_width=True)
        st.metric(label="Total Revenue (RM)", value=f"{total_revenue:.2f}")
    with col2:
        kpi_chart = alt.hconcat(total_orders_card)
        st.altair_chart(kpi_chart, use_container_width=True)
        st.metric(label="Total Orders", value=total_orders)
    with col3:
        kpi_chart = alt.hconcat(average_order_value_card)
        st.altair_chart(kpi_chart, use_container_width=True)
        st.metric(label="Average Order Value (RM)", value=f"{average_order_value:.2f}")
    with col4:
        kpi_chart = alt.hconcat(total_items_sold_card)
        st.altair_chart(kpi_chart, use_container_width=True)
        st.metric(label="Total Items Sold", value=total_items_sold)
    
    # Subheading
    st.markdown('')
    st.markdown("<h2 style='text-align: left; color: orange;'>Today's Order and Sales Analytics</h2>", unsafe_allow_html=True)

     # Search for Order Number
    order_number_search = st.text_input("Search Order Number", "")
    if order_number_search:
        today_orders = today_orders[today_orders['Order Number'].astype(str).str.contains(order_number_search)]

    # Allow admin to filter by status
    status_filter = st.selectbox("Filter by Order Status", options=["All"] + today_orders['Status'].unique().tolist())
    
    if status_filter != "All":
        today_orders = today_orders[today_orders['Status'] == status_filter]

    # Group by 'Order Number' and concatenate items
    grouped_orders = today_orders.groupby(['Order Number', 'Username', 'Status']).agg(
        Items=('Item', lambda x: ', '.join(x)),
        Total_Price=('Price', 'sum')
    ).reset_index()

    # Format Total_Price to 2 decimal places
    grouped_orders['Total_Price'] = grouped_orders['Total_Price'].map("{:.2f}".format)

    # Display the results
    st.markdown("<div class='subheading'>Today's Orders</div>", unsafe_allow_html=True)
    st.dataframe(grouped_orders)
    
    # Display order counts for each status
    st.markdown('')
    st.subheader("Today's Order Status Distribution (Latest Status)")

    # Keep only the most recent status for each order number
    latest_status_orders = original_today_orders.sort_values(by=['Order Number', 'Time']).groupby('Order Number').tail(1)

    # Count order statuses based on the latest status
    latest_order_status_counts = latest_status_orders['Status'].value_counts().reset_index()
    latest_order_status_counts.columns = ['Status', 'Count']

    # Exclude 'Received' orders from the counts for pie and bar charts
    filtered_status_counts = latest_order_status_counts[latest_order_status_counts['Status'] != 'Received']

    # Expander for Pie Chart with Altair
    with st.expander("Pie Chart"):
        pie_chart = alt.Chart(filtered_status_counts).mark_arc().encode(
            theta=alt.Theta(field='Count', type='quantitative'),
            color=alt.Color(field='Status', type='nominal'),
            tooltip=['Status', 'Count']
        ).properties(
            title="Today's Order Status Distribution",
            width=700,
            height=400
        )
        st.altair_chart(pie_chart, use_container_width=True)

    # Expander for Bar Chart with Altair
    with st.expander("Bar Chart"):
        bar_chart = alt.Chart(filtered_status_counts).mark_bar().encode(
            x=alt.X('Status:O', title='Order Status', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Count:Q', title='Number of Orders'),  
            color=alt.Color('Status:N', legend=None),
            tooltip=['Status', 'Count']
        ).properties(
            title="Today's Order Status Counts",
            width=700,
            height=400
        )
        st.altair_chart(bar_chart, use_container_width=True)


    # ------------------ Define Inventory Function ------------------ #
    # Initialize inventory in session state if it doesn't exist
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "Coffee Beans (g)": 200,        
            "Milk (ml)": 100,               
            "Sugar (g)": 50,                
            "Cups": 20,                     
            "Bread (g)": 200,               
            "Cheese (g)": 50,               
            "Lettuce (g)": 50,              
            "Tomatoes (g)": 50,             
            "Pasta (g)": 200,               
            "Pasta Sauce (ml)": 150,        
            "Eggs": 12,                     
            "Pastry Sheets": 10,            
            "Condensed Milk (ml)": 200,     
        }

    # ------------------ Define Restock List Function ------------------ #
    def restock_list(inventory):
        low_inventory_items = []

        # Define thresholds for restocking
        thresholds = {
            "Coffee Beans (g)": 160,
            "Milk (ml)": 80,
            "Sugar (g)": 40,
            "Cups": 16,
            "Bread (g)": 160,
            "Cheese (g)": 40,
            "Lettuce (g)": 40,
            "Tomatoes (g)": 40,
            "Pasta (g)": 160,
            "Pasta Sauce (ml)": 120,
            "Eggs": 9,
            "Pastry Sheets": 8,
            "Condensed Milk (ml)": 160,
        }

        # Check inventory levels
        for item, qty in inventory.items():
            if qty < thresholds[item]:
                low_inventory_items.append(item)
        
        return low_inventory_items

    # ------------------ Inventory Dashboard ------------------ #
    st.markdown('')
    st.markdown("<h2 style='text-align: left; font-size: 40px; color: orange;'>Inventory Dashboard</h2>", unsafe_allow_html=True)

    # Inventory Levels
    st.markdown("<div class='subheading'>Current Inventory Levels</div>", unsafe_allow_html=True)
    inventory_df = pd.DataFrame(st.session_state.inventory.items(), columns=["Item", "Quantity"])
    st.dataframe(inventory_df)

    # Low Inventory Alerts
    low_inventory_items = restock_list(st.session_state.inventory)  # Call the function with the current inventory
    if low_inventory_items:
        st.markdown("<span style='color:red;'>⚠️ Items that need restocking:</span>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(low_inventory_items, columns=['Item']))
    else:
        st.write("All items are sufficiently stocked.")

    # ------------------ Inventory Health Check Charts ------------------ #
    st.markdown("<div class='subheading'>Inventory Health Check</div>", unsafe_allow_html=True)

    # Add threshold values and stock status to the inventory DataFrame
    thresholds = {
        "Coffee Beans (g)": 160,
        "Milk (ml)": 80,
        "Sugar (g)": 40,
        "Cups": 16,
        "Bread (g)": 160,
        "Cheese (g)": 40,
        "Lettuce (g)": 40,
        "Tomatoes (g)": 40,
        "Pasta (g)": 160,
        "Pasta Sauce (ml)": 120,
        "Eggs": 9,
        "Pastry Sheets": 8,
        "Condensed Milk (ml)": 160,
    }

    inventory_df['Threshold'] = inventory_df['Item'].map(thresholds)
    inventory_df['Status'] = inventory_df.apply(
        lambda row: 'Low' if row['Quantity'] < row['Threshold'] else 
                    ('Medium' if row['Quantity'] <= row['Threshold'] + 15 else 'High'), 
        axis=1
    )

    # ------------------ Inventory Health Check (Bar Chart) ------------------ #
    with st.expander("Inventory Health Check (Bar Chart)"):
        st .write("This bar chart shows current inventory levels, with colors indicating stock status compared to threshold levels.")

        # Create interactive Altair bar chart
        bar_chart = alt.Chart(inventory_df).mark_bar().encode(
            x=alt.X('Item', sort='-y', title="Inventory Items"),
            y=alt.Y('Quantity', title="Quantity in Stock"),
            color=alt.Color('Status', scale=alt.Scale(domain=['Low', 'Medium', 'High'], range=['red', 'orange', 'green'])),
            tooltip=['Item', 'Quantity', 'Threshold', 'Status']
        ).properties(width=700, height=400).interactive()

        st.altair_chart(bar_chart, use_container_width=True)