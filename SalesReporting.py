import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm

def sales_reporting(dataset):
    # Load order history data
    df = pd.read_csv(dataset)

    # Convert 'Time' column to datetime for easier analysis
    df['Time'] = pd.to_datetime(df['Time'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    df = df.dropna(subset=['Time'])

    # Calculate Total Cancelled Orders
    cancelled_orders = df[df['Status'] == "Cancelled"]
    total_cancelled_orders = cancelled_orders['Order Number'].nunique()  # Count unique order numbers

    # Calculate Total Completed Orders
    completed_orders = df[df['Status'] == "Completed"]
    total_completed_orders = completed_orders['Order Number'].nunique()  # Count unique order numbers

    # Calculate total sales and revenue from completed orders
    total_sales = completed_orders['Quantity'].sum()
    total_revenue = completed_orders['Price'].sum()

    # Define unit costs for each inventory item
    unit_costs = {
        "Coffee Beans (g)": 0.05,
        "Milk (ml)": 0.03,
        "Sugar (g)": 0.02,
        "Cups": 0.10,
        "Bread (g)": 0.04,
        "Cheese (g)": 0.10,
        "Lettuce (g)": 0.03,
        "Tomatoes (g)": 0.05,
        "Pasta (g)": 0.04,
        "Pasta Sauce (ml)": 0.05,
        "Eggs": 0.30,
        "Pastry Sheets": 0.50,
        "Condensed Milk (ml)": 0.04
    }

    # Calculate inventory cost for completed orders
    inventory_cost = 0
    inventory_usage = {
        "Americano": {"Coffee Beans (g)": 10, "Cups": 1},
        "Cappuccino": {"Coffee Beans (g)": 10, "Milk (ml)": 50, "Cups": 1},
        "Latte": {"Coffee Beans (g)": 10, "Milk (ml)": 50, "Cups": 1},
        "Caramel Macchiato": {"Coffee Beans (g)": 10, "Milk (ml)": 50, "Cups": 1},
        "Sandwich": {"Bread (g)": 100, "Cheese (g)": 20, "Lettuce (g)": 10, "Tomatoes (g)": 10},
        "Pasta": {"Pasta (g)": 150, "Pasta Sauce (ml)": 50},
        "Egg Tart": {"Eggs": 1, "Pastry Sheets": 1, "Condensed Milk (ml)": 30}
    }

    # Calculate total inventory cost based on completed orders
    for index, row in completed_orders.iterrows():
        item = row['Item'].split(" (")[0]
        quantity = row['Quantity']

        if item in inventory_usage:
            for ingredient, amount in inventory_usage[item].items():
                if ingredient in unit_costs:
                    inventory_cost += amount * quantity * unit_costs[ingredient]

    # Calculate profit
    profit = total_revenue - inventory_cost

    st.markdown(
        """
        <h1 style="text-align: center;">Sales Reporting Dashboard</h1>
        <br>
        """,
        unsafe_allow_html=True
    )

    # Overall sales and revenue
    st.header("Overall Sales Performance")

    # Layout for total sales and revenue
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Completed Orders", total_completed_orders)  # Display unique completed orders
        st.metric("Total Revenue (RM)", f"{total_revenue:.2f}")
        
    with col2:
        st.metric("Total Cancelled Orders", total_cancelled_orders)  # Display unique cancelled orders
        st.metric("Total Inventory Cost (RM)", f"{inventory_cost:.2f}")
        st.metric("Profit (RM)", f"{profit:.2f}")

    # Daily Sales
    completed_orders['Date'] = completed_orders['Time'].dt.date
    daily_sales = completed_orders.groupby('Date')['Price'].sum().reset_index()
    recent_7_days = daily_sales.tail(7)

    # Sales Insights
    st.header("Sales Insights")

    # Plot daily sales
    st.subheader("Daily Sales")

    with st.expander("Table"):
        st.dataframe(daily_sales, width=1200)

    with st.expander("Line Chart"):
        plt.figure(figsize=(10, 5))
        plt.plot(daily_sales['Date'], daily_sales['Price'], marker='o')
        plt.xlabel("Date")
        plt.ylabel("Revenue (RM)")
        plt.title("Daily Sales Revenue - Line Chart", fontweight='bold')
        st.pyplot(plt)

    with st.expander("Bar Graph"):
        plt.figure(figsize=(10, 5))
        plt.bar(recent_7_days['Date'].astype(str), recent_7_days['Price'], color='blue')
        plt.xlabel("Date")
        plt.ylabel("Revenue (RM)")
        plt.title("Daily Sales Revenue - Bar Graph", fontweight='bold')
        st.pyplot(plt)

    # Weekly Sales
    completed_orders['Week'] = completed_orders['Time'].dt.to_period('W').apply(lambda r: r.start_time)
    weekly_sales = completed_orders.groupby('Week')['Price'].sum().reset_index()
    weekly_sales['Week Range'] = weekly_sales['Week'].dt.strftime('%Y-%m-%d') + " to " + (weekly_sales['Week'] + pd.Timedelta(days=6)).dt.strftime('%Y-%m-%d')

    # Plot weekly sales
    st.subheader("Weekly Sales")

    with st.expander("Table"):
        st.dataframe(weekly_sales[['Week Range', 'Price']], width=1200)

    with st.expander("Line Chart"):
        plt.figure(figsize=(10, 5))
        plt.plot(weekly_sales['Week Range'], weekly_sales['Price'], marker='o', color=cm.inferno(0.75))
        plt.xticks(rotation=45, ha='right')
        plt.xlabel("Week Range")
        plt.ylabel("Revenue (RM)")
        plt.title("Weekly Sales Revenue - Line Chart", fontweight='bold')
        st.pyplot(plt)

    with st.expander("Bar Graph"):
        plt.figure(figsize=(10, 5))
        plt.bar(weekly_sales['Week Range'], weekly_sales['Price'], color='orange')
        plt.xticks(rotation=45, ha='right')
        plt.xlabel("Week Range")
        plt.ylabel("Revenue (RM)")
        plt.title("Weekly Sales Revenue - Bar Graph", fontweight='bold')
        st.pyplot(plt)

    # Monthly Sales
    completed_orders['Month'] = completed_orders['Time'].dt.month_name()
    monthly_sales = completed_orders.groupby('Month')['Price'].sum().reset_index()

    # Define the order of months in a calendar year
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Convert 'Month' column to a categorical type with the specified order
    monthly_sales['Month'] = pd.Categorical(monthly_sales['Month'], categories=month_order, ordered=True)

    # Sort the DataFrame by month
    monthly_sales = monthly_sales.sort_values(by='Month').reset_index(drop=True)

    # Plot monthly sales
    st.subheader("Monthly Sales")

    with st.expander("Table"):
        st.dataframe(monthly_sales, width=1200)

    with st.expander("Line Chart"):
        plt.figure(figsize=(10, 5))
        plt.plot(monthly_sales['Month'], monthly_sales['Price'], marker='o', color=cm.inferno(0.25))
        plt.xlabel("Month")
        plt.ylabel("Revenue (RM)")
        plt.title("Monthly Sales Revenue - Line Chart", fontweight='bold')
        st.pyplot(plt)

    with st.expander("Bar Graph"):
        plt.figure(figsize=(10, 5))
        plt.bar(monthly_sales['Month'], monthly_sales['Price'], color='purple')
        plt.xlabel("Month")
        plt.ylabel("Revenue (RM)")
        plt.title("Monthly Sales Revenue - Bar Graph", fontweight='bold')
        st.pyplot(plt)

# Product Performance
    st.header("Product Performance")

    # Top and least-performing products based on completed orders
    product_sales = completed_orders.groupby('Item')['Quantity'].sum().sort_values(ascending=False).reset_index()
    top_product = product_sales.iloc[0] if not product_sales.empty else None
    least_product = product_sales.iloc[-1] if not product_sales.empty else None

    # Define image paths for each product
    product_images = {
        "Americano": "Resource/americano.png",
        "Cappuccino": "Resource/cappucino.jpg",
        "Latte": "Resource/latte.jpg",
        "Caramel Macchiato": "Resource/caramelMacchiato.jpg",
        "Sandwich": "Resource/sandwich.jpg",
        "Pasta": "Resource/pasta.jpg",
        "Egg Tart": "Resource/eggTart.jpg"
    }

    # Helper function to extract main product name
    def extract_product_name(item_name):
        return item_name.split(" (")[0].strip()

    col6, col7 = st.columns(2)
    with col6:
        if top_product is not None:
            st.subheader("Top-Performing Product")
            top_product_name = extract_product_name(top_product['Item'])
            top_product_image = product_images.get(top_product_name, None)
            if top_product_image:
                st.image(top_product_image, width=150)
            st.write(f"{top_product['Item']} with {top_product['Quantity']} units sold")

    with col7:
        if least_product is not None:
            st.subheader("Least-Performing Product")
            least_product_name = extract_product_name(least_product['Item'])
            least_product_image = product_images.get(least_product_name, None)
            if least_product_image:
                st.image(least_product_image, width=150)
            st.write(f"{least_product['Item']} with {least_product['Quantity']} units sold")