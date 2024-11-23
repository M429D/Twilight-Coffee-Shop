import random
from datetime import datetime
import pandas as pd
import streamlit as st
from Notify import NotifyCustomer, NotifyStaff
from Pay import create_checkout_session
from datetime import datetime, timedelta
import time
from io import BytesIO
from decimal import Decimal, ROUND_DOWN
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# ------------------ Initialize Global Variables ------------------ #
if 'order_history' not in st.session_state:
    st.session_state.order_history = pd.DataFrame(columns=['Order Number', 'Item', 'Quantity', 'Price', 'Time', 'Status'])
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
if 'order_placed' not in st.session_state:
    st.session_state.order_placed = False

if 'current_page' not in st.session_state:
    st.session_state.current_page = "food"

# ------------ Get Membership Points -------------- #
def get_membership_points(username, EXCEL_FILE):
    # Read the existing Excel file into a DataFrame
    df = pd.read_excel(EXCEL_FILE)
    
    # Check if the user exists in the DataFrame
    if username in df['Username'].values:
        # Retrieve the current membership points of the user
        current_points = df.loc[df['Username'] == username, 'Membership Points'].iloc[0]
        
        # Return the current points
        return current_points
    else:
        st.error(f"User with username '{username}' not found.")
        return None  # If user is not found, return None

# ------------ Update Membership Points -------------- #
def update_membership_points(username, points_change, EXCEL_FILE):
    # Read the existing Excel file into a DataFrame
    df = pd.read_excel(EXCEL_FILE)
    
    # Check if the user exists in the DataFrame
    if username in df['Username'].values:
        # Get the current membership points of the user
        current_points = df.loc[df['Username'] == username, 'Membership Points'].iloc[0]
        
        # Calculate the new membership points based on the points change (positive or negative)
        new_points = current_points + points_change
        
        # Update the membership points for the user
        df.loc[df['Username'] == username, 'Membership Points'] = new_points
        
        # Save the updated DataFrame back to the Excel file
        df.to_excel(EXCEL_FILE, index=False)
        
        # Provide feedback to the user
        if points_change > 0:
            st.success(f"{points_change} points have been added. {username}'s new total is {new_points} points.")
        elif points_change < 0:
            st.success(f"{abs(points_change)} points have been redeemed. {username}'s new total is {new_points} points.")
        else:
            st.warning(f"No points change for {username}.")
    else:
        st.error(f"User with username '{username}' not found.")

# ------------ Save Order History -------------- #
def save_order_history():
    if 'order_history' in st.session_state:
        # Define a unified file to store all users' order history
        filename = "all_users_order_history.csv"

        # Check if order history DataFrame is not empty
        if not st.session_state['order_history'].empty:
            # Load existing data if the file already exists
            try:
                existing_data = pd.read_csv(filename)
            except FileNotFoundError:
                # If file doesn't exist, start with an empty DataFrame
                existing_data = pd.DataFrame(columns=st.session_state['order_history'].columns)

            # Append the current session's order history to the existing data
            updated_data = pd.concat([existing_data, st.session_state['order_history']], ignore_index=True)

            # Save the combined data back to the CSV file
            updated_data.to_csv(filename, index=False)

        else:
            st.warning("No order history found to save.")

    else:
        st.warning("Order history data is not available in the session state.")


# ------------ Display Order History -------------- #
def display_user_order_history(EXCEL_FILE):
    
    # Initialize NotifyStaff instance
    notifier = NotifyCustomer()
    cntrNotify = st.container()

    st.markdown(
        """
        <h1 style="text-align: center;">Your Order History</h1>
        <br>
        """,
        unsafe_allow_html=True
    )
    
    if 'username' in st.session_state:
        username = st.session_state.get("username")
        try:
            # Load the unified order history CSV file
            filename = "all_users_order_history.csv"
            all_orders = pd.read_csv(filename)

            # Filter orders based on the logged-in user's username
            user_orders = all_orders[all_orders["Username"] == st.session_state.username]

            # Reset the index of the filtered DataFrame
            user_orders = user_orders.reset_index(drop=True)

            # Display the order history if it exists
            if not user_orders.empty:
                # Sort orders by "Time" to get the latest order
                user_orders["Time"] = pd.to_datetime(user_orders["Time"])

                # Get the latest order's number based on the most recent time
                latest_order = user_orders.sort_values("Time", ascending=False).iloc[0]
                latest_order_number = latest_order["Order Number"]

                # Display the user's order history
                st.dataframe(user_orders)

                # Filter orders with the same order number, and sort by "Status Priority" and "Time"
                # Define custom priority mapping for order statuses
                status_priority = {
                    "Completed": 3,
                    "Cancelled": 2,
                    "Processing": 1,
                    "Received": 0
                }

                # Add a new column to represent the status priority
                user_orders["Status Priority"] = user_orders["Status"].map(status_priority)

                # Filter the orders with the same "Order Number" as the latest one
                same_order_number = user_orders[user_orders["Order Number"] == latest_order_number]

                # Sort by "Status Priority" (highest priority first), then by "Time" (most recent first)
                latest_order = same_order_number.sort_values(by=["Status Priority", "Time"], ascending=[False, False]).iloc[0]
                latest_order_status = latest_order["Status"]

                # Display current membership points
                membership_points = get_membership_points(username, EXCEL_FILE)
                st.markdown(f"<p style='color: orange;'>Current Membership Points: {membership_points}</p>", unsafe_allow_html=True)

                # Notify based on the status of the latest order
                if latest_order_status == "Completed":
                    notifier.order_ready_notification(latest_order_number, cntrNotify)
                elif latest_order_status == "Cancelled":
                    notifier.order_cancel_notification(latest_order_number, cntrNotify)
                elif latest_order_status == "Processing":
                    notifier.order_processing_notification(latest_order_number, cntrNotify)
            else:
                st.markdown("<p style='color: orange;'>You have no order history.</p>", unsafe_allow_html=True)
                st.markdown("<p style='color: orange;'>Please go to the order page to place your order! ☕</p>", unsafe_allow_html=True)

        except (FileNotFoundError, KeyError):
            st.markdown("<p style='color: orange;'>You have no order history.</p>", unsafe_allow_html=True)
            st.markdown("<p style='color: orange;'>Please go to the order page to place your order! ☕</p>", unsafe_allow_html=True)

    else:
        st.warning("Please log in to view your order history.")




# ------------------ Define Restock List Function ------------------ #
def restock_list():
    low_inventory_items = []

    # Define thresholds for restocking
    thresholds = {
        "Coffee Beans (g)": 160,        # Used in Americano, Latte, Caramel Macchiato, and Cappuccino
        "Milk (ml)": 80,                # Used in Latte, Caramel Macchiato, and Cappuccino
        "Sugar (g)": 40,                # Optional for all coffee drinks
        "Cups": 16,                     # Required for all drinks
        "Bread (g)": 160,               # Used in Sandwich
        "Cheese (g)": 40,               # Optional ingredient for Sandwich
        "Lettuce (g)": 40,              # Optional ingredient for Sandwich
        "Tomatoes (g)": 40,             # Optional ingredient for Sandwich
        "Pasta (g)": 160,               # Used in Pasta
        "Pasta Sauce (ml)": 120,        # Used in Pasta
        "Eggs": 9,                      # Used in Egg Tart (e.g., 1 egg per tart)
        "Pastry Sheets": 8,             # Used in Egg Tart (e.g., 1 sheet per tart)
        "Condensed Milk (ml)": 160,     # Used in Egg Tart (or regular milk depending on recipe)
    }

    # Check inventory levels
    for item, qty in st.session_state.inventory.items():
        if qty < thresholds[item]:
            low_inventory_items.append(item)
    
    return low_inventory_items


# ------------------ Define the Reduce Inventory Function ------------------ #
def reduce_inventory(item, quantity, milk=False, sugar=False):

    # Reducing inventory based on the item and quantity ordered
    if "Americano" in item or "Latte" in item or "Caramel Macchiato" in item or "Cappuccino" in item:
        st.session_state.inventory["Coffee Beans (g)"] -= 10 * quantity  # Assuming 10g of coffee beans per coffee
        st.session_state.inventory["Cups"] -= quantity  # One cup per coffee
        if milk:
            st.session_state.inventory["Milk (ml)"] -= 50 * quantity  # Assuming 50ml of milk for Latte/Macchiato/Cappuccino
        if sugar:
            st.session_state.inventory["Sugar (g)"] -= 5 * quantity  # Assuming 5g of sugar per coffee

    elif item == "Sandwich":
        st.session_state.inventory["Bread (g)"] -= 100 * quantity  # Assuming 100g of bread per sandwich
        # Optional ingredients for Sandwich
        st.session_state.inventory["Cheese (g)"] -= 20 * quantity  # Assuming 20g of cheese per sandwich
        st.session_state.inventory["Lettuce (g)"] -= 10 * quantity  # Assuming 10g of lettuce per sandwich
        st.session_state.inventory["Tomatoes (g)"] -= 10 * quantity  # Assuming 10g of tomatoes per sandwich

    elif item == "Pasta":
        st.session_state.inventory["Pasta (g)"] -= 150 * quantity  # Assuming 150g of pasta per serving
        st.session_state.inventory["Pasta Sauce (ml)"] -= 50 * quantity  # Assuming 50ml of sauce per serving

    elif item == "Egg Tart":
        st.session_state.inventory["Eggs"] -= quantity  # Assuming 1 egg per tart
        st.session_state.inventory["Pastry Sheets"] -= quantity  # Assuming 1 pastry sheet per tart
        st.session_state.inventory["Condensed Milk (ml)"] -= 30 * quantity  # Assuming 30ml of condensed milk per tart



# ------------------ Function to generate PDF receipt from order history DataFrame------------------ #
def generate_pdf_receipt(order_number, total_amount, promo_discount_amount=0, points_used=0, points_conversion_rate=100):
    buffer = BytesIO()
    # Create a canvas
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Add logo
    logo_path = "Resource/LOGO PNG.png"
    try:
        p.drawImage(logo_path, width / 2.0 - 50, height - 125, width=100, height=100, mask='auto')
    except Exception as e:
        print(f"Error loading logo: {e}")

    p.setFont("Times-Roman", 30)
    p.drawCentredString(width / 2.0, height - 150, "Twilight Coffee Shop")

    p.setFont("Times-Roman", 12)
    now = datetime.now()
    receipt_id = f"R{now.strftime('%Y%m%d%H%M%S')}"
    p.drawString(50, height - 200, f"Receipt ID: {receipt_id}")
    p.drawString(50, height - 215, f"Date: {now.strftime('%d/%m/%Y')}")
    p.drawString(50, height - 230, f"Time: {now.strftime('%H:%M:%S')}")
    p.drawString(50, height - 245, f"Order Number: {order_number}")  # Order Number under Time


    # Table heading
    table_data = [["Item", "Quantity", "Price (RM)", "Subtotal (RM)"]]
    order_details = st.session_state.order_history[st.session_state.order_history["Order Number"] == order_number]

    # Table content from the order details
    for _, row in order_details.iterrows():
        item = row["Item"]
        quantity = row["Quantity"]
        price = row["Price"] / row["Quantity"]
        subtotal = row["Price"]
        table_data.append([item, quantity, f"{price:.2f}", f"{subtotal:.2f}"])

    # Initialize total discount
    total_discount = promo_discount_amount

    # Calculate and display discount amounts
    if points_used > 0:  # Check if points were used
        points_discount_amount = points_used / points_conversion_rate
        total_discount += points_discount_amount
        table_data.append([f"Points Used: {points_used}", "", "", f"RM {points_discount_amount:.2f}"])

    if promo_discount_amount > 0:
        table_data.append([f"Promo Discount:", "", "", f"RM {promo_discount_amount:.2f}"])

    # Add total discount row
    # table_data.append(["Total Discount:", "", "", f"RM {total_discount:.2f}"])

    # Calculate Grand Total
    grand_total = total_amount - total_discount
    table_data.append(["Grand Total:", "", "", f"RM {grand_total:.2f}"])

    # Table creation
    table = Table(table_data, colWidths=[310, 50, 60, 80])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Center text vertically
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),  # Set header row font to bold
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),  # Set the rest of the table to regular font
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('SPAN', (0, -1), (2, -1)),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, -1), (2, -1), 'RIGHT')
    ]))

    # Fixed starting height from the top of the page for the first row of the table
    fixed_table_start_y = 380  # Adjust this to your desired starting position

    # Wrap the table to calculate its size without drawing it
    table.wrapOn(p, width, height)

    # Always start the table at the fixed position, regardless of its size
    table.drawOn(p, 50, fixed_table_start_y)

    # Footer with shop address and contact
    p.drawString(50, 85, "Universiti Teknologi PETRONAS (UTP)")
    p.drawString(50, 70, "32610 Seri Iskandar, Perak Darul Ridzuan, Malaysia")
    p.drawString(50, 55, "Support Line: +60-162114744")

    # Finalize and save the PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    # Set the file name dynamically based on order number
    buffer.file_name = f"{order_number}_Receipt.pdf"
    
    return buffer

    
        
# ------------------ Take Order Function ------------------ #
def take_order():
    # Initialize NotifyStaff instance
    notifier = NotifyCustomer()
    cntrNotify = st.container()

    if not st.session_state.order_placed:
        st.markdown(
            """
            <h1 style="text-align: center;">Order Your Items</h1>
            <br>
            """,
            unsafe_allow_html=True
        )

        # Menu
        coffee_menu = {
            "Americano": 11.00,
            "Cappuccino": 12.00,
            "Latte": 12.00,
            "Caramel Macchiato": 14.00
        }
        food_menu = {
            "Sandwich": 11.00,
            "Pasta": 14.00,
            "Egg Tart": 6.00
        }

         # Create two columns for food and coffee menus with custom widths
        col1, col2 = st.columns([1, 2])  # Adjust the number here for column widths

        # Add a large gap between columns
        st.write("<div style='height: 50px;'></div>", unsafe_allow_html=True)  # Space between the columns


        # Display food menu in the left column
        with col1:
            st.markdown("<div class='subheading' style='font-size: 40px;  color: gold; margin-top: 20px;'>Food Menu</div>", unsafe_allow_html=True)
            selected_foods = st.multiselect("Select your food :knife_fork_plate:", list(food_menu.keys()), key="selected_foods")
            food_orders = {}
            for food in selected_foods:
                quantity = st.number_input(f"Select quantity for {food}", min_value=1, step=1, key=f"{food}_qty")
                food_orders[food] = {'quantity': quantity}

        # Display coffee menu in the right column
        with col2:
            st.markdown("<div class='subheading' style='font-size: 40px;  color: gold; margin-top: 20px;'>Coffee Menu</div>", unsafe_allow_html=True)
            selected_coffees = st.multiselect("Select your coffee :coffee:", list(coffee_menu.keys()), key="selected_coffees")
            coffee_orders = {}
            for coffee in selected_coffees:
                quantity = st.number_input(f"Select quantity for {coffee}", min_value=1, step=1, key=f"{coffee}_qty")
                size = st.radio(f"Choose size for {coffee}", ["Small", "Medium", "Large"], key=f"{coffee}_size")
                temperature = st.radio(f"Choose temperature for {coffee}", ["Hot", "Cold"], key=f"{coffee}_temp")
                sugar = st.checkbox(f"Extra Sugar for {coffee}", key=f"{coffee}_sugar")
                noSugar= st.checkbox(f"No Sugar for {coffee}", key=f"{coffee}_noSugar")
                milk = st.checkbox(f"Add Milk for {coffee}", key=f"{coffee}_milk")
                noMilk= st.checkbox(f"No Milk for {coffee}", key=f"{coffee}_noMilk")
                coffee_orders[coffee] = {
                    'quantity': quantity,
                    'size': size,
                    'temperature': temperature,
                    'sugar': sugar,
                    'noSugar': noSugar,
                    'milk': milk,
                    'noMilk': noMilk
                }

    
        # Extra Request Section
        st.markdown("<div class='subheading' style='font-size: 20px;  color: orange; margin-top: 20px;'>Extra Requests</div>", unsafe_allow_html=True)
        extra_request = st.text_input("Please specify any extra requests.", key="extra_request")

        promo_discount_amount = Decimal(0)
        points_discount_amount = Decimal(0)
        promo_discount_percentage = Decimal(0)
        points_to_use = 0
        points_conversion_rate = Decimal(100)  # Example: 100 points = RM1

        # Calculate total price for all selected items
        total_price = Decimal(0)
        selected_items_with_quantities = [] 
        discounted_prices = []  # To store discounted prices for each item

        # Calculate total number of items
        total_items = sum(details['quantity'] for details in coffee_orders.values()) + sum(details['quantity'] for details in food_orders.values())

        # Calculate the total amount for the points discount (calculate once here)
        if total_items > 0:
            points_discount_amount = (Decimal(points_to_use) / points_conversion_rate).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

        # Debugging: Print the total points discount
        print(f"Total Points Discount: RM {points_discount_amount:.2f}")

        # Calculate prices and discounts per item
        all_items = list(coffee_orders.items()) + list(food_orders.items())  # Combine coffee and food into one list

        # Calculate the total amount before distributing points discount
        for item, details in all_items:
            if item in coffee_orders:  # Coffee item
                price = Decimal(coffee_menu[item]) * details['quantity']
            else:  # Food item
                price = Decimal(food_menu[item]) * details['quantity']

            # Promo Discount
            promo_discount_amount_per_item = (promo_discount_percentage / Decimal(100)) * price
            promo_discount_amount_per_item = promo_discount_amount_per_item.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

            # Apply Points Discount proportionally (distribute points discount across all items)
            item_points_discount_amount = (points_discount_amount / Decimal(total_items) * details['quantity']) if total_items > 0 else Decimal(0)
            item_points_discount_amount = item_points_discount_amount.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

            # Final Discounted Price per item
            discounted_price = price - promo_discount_amount_per_item - item_points_discount_amount
            discounted_price = discounted_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

            # Add to the total price
            total_price += discounted_price
            discounted_prices.append(discounted_price)
            selected_items_with_quantities.append((item, discounted_price, details['quantity']))

        st.write(f"Total Amount: RM {total_price:.2f}")

        # Display available promo codes
        if 'promotions' in st.session_state and st.session_state.promotions:
            st.markdown("<h3 style='color: #4CAF50;'>Available Promo Codes</h3>", unsafe_allow_html=True)
            promo_codes_df = pd.DataFrame.from_dict(st.session_state.promotions, orient='index').reset_index()
            promo_codes_df.columns = ['Promo Code', 'Description', 'Discount Percentage (%)', 'Min Purchase', 'Starting Date', 'Expiration Date']

            # Convert date columns to datetime for filtering
            promo_codes_df['Starting Date'] = pd.to_datetime(promo_codes_df['Starting Date'])
            promo_codes_df['Expiration Date'] = pd.to_datetime(promo_codes_df['Expiration Date'])
            
            # Convert 'Min Purchase' to numeric
            promo_codes_df['Min Purchase'] = pd.to_numeric(promo_codes_df['Min Purchase'], errors='coerce')

            # Get current date
            current_date = datetime.now()

            # Filter promo codes based on current date and minimum purchase
            filtered_promo_codes = promo_codes_df[
                (promo_codes_df['Starting Date'] <= current_date) &
                (promo_codes_df['Expiration Date'] >= current_date) &
                (promo_codes_df['Min Purchase'] <= total_price)
            ]

            # Create string representations of the dates for display
            promo_codes_df['Start Date'] = promo_codes_df['Starting Date'].dt.strftime('%Y-%m-%d')
            promo_codes_df['End Date'] = promo_codes_df['Expiration Date'].dt.strftime('%Y-%m-%d')

            # Display the DataFrame using Streamlit's built-in function
            st.dataframe(promo_codes_df[['Promo Code', 'Description', 'Discount Percentage (%)', 'Min Purchase', 'Start Date', 'End Date']].style.set_table_attributes('style="white-space: nowrap;"').set_table_styles(
                [{'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]}]
            ))

            # Check if there are any valid promo codes
            if not filtered_promo_codes.empty:
                # Let the user select a promo code
                selected_promo_code = st.selectbox("Select a promo code:", filtered_promo_codes['Promo Code'])

                # Get the selected promo code details
                selected_details = filtered_promo_codes[filtered_promo_codes['Promo Code'] == selected_promo_code].iloc[0]

                # Apply the discount based on the percentage
                promo_discount_percentage = Decimal(int(selected_details['Discount Percentage (%)']))
                promo_discount_amount = (promo_discount_percentage / Decimal(100)) * total_price
                promo_discount_amount = promo_discount_amount.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                st.markdown(f"<div style='background-color: #333333; color: #FFFFFF; padding: 10px; border-radius: 5px;'>"
                    f"<strong>Discount Amount from Promo Code:</strong> RM {promo_discount_amount:.2f}</div>", unsafe_allow_html=True)
                total_price -= promo_discount_amount
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Get user points
        username = st.session_state.username  
        POINTS = 'TWILIGHT_USERS.xlsx'
        user_points = get_membership_points(username, POINTS)  
        points_conversion_rate = Decimal(100)  # Example: 100 points = RM1
        max_discount = user_points / points_conversion_rate  # Maximum discount they can apply

        st.write(f"Your Points: {user_points} (Can convert to RM {max_discount:.2f})")

        # Option to apply points
        apply_points = st.checkbox("Apply points as discount")
        if apply_points:
            points_to_use = st.number_input("Enter points to use", min_value=0, max_value=user_points)
            points_discount_amount = (Decimal(points_to_use) / points_conversion_rate).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            if points_discount_amount > total_price:
                st.error("You cannot apply more points than the total price.")
            else:
                total_price -= points_discount_amount
                st.success(f"Discount applied! New total: RM {total_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN):.2f}")
                st.session_state.points_to_use = points_to_use  # Store points to use in session state
                # Display points discount in a styled box
                st.markdown(f"<div style='background-color: #333333; color: #FFFFFF; padding: 10px; border-radius: 5px;'>"
                            f"<strong>Discount Amount from Points:</strong> RM {points_discount_amount:.2f}</div>", unsafe_allow_html=True)
        else:
            st.session_state.points_to_use = 0  # Reset if not applying points

        st.markdown(f"<div style='background-color: #333333; color: #FFFFFF; padding: 10px; border-radius: 5px;'>"
            f"<strong>Total Discounts Applied:</strong> RM {promo_discount_amount + points_discount_amount:.2f}</div>", unsafe_allow_html=True)

        # Show the final total after all discounts
        grand_total = total_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        st.markdown(f"<h2 style='color: green; font-size: 40px;'>Grand Total: RM {grand_total:.2f}</h2>", unsafe_allow_html=True)
        
        # Calculate the total number of items
        # total_items = sum(details['quantity'] for details in coffee_orders.values()) + sum(details['quantity'] for details in food_orders.values())

        # Place Order Button
        if st.button("Place Order"):
            # Create checkout session
            session = create_checkout_session(selected_items_with_quantities,promo_discount_percentage,points_discount_amount)

            if session:
                # Display the payment link and start the timer
                st.markdown(f"[Click here]({session.url}) to proceed with payment.", unsafe_allow_html=True)
                st.write("Payment in progress (Time limit: 5 minutes)")
                time.sleep(10)
                
                # Record the current time for countdown
                payment_start_time = datetime.now()
                st.session_state.payment_start_time = payment_start_time
            else:
                st.error("Failed to create payment session. Please try again in 5 seconds.")
                time.sleep(5)
                st.session_state.order_placed = False
                st.rerun()

        # Ask the user to confirm payment if the session is active
        if "payment_start_time" in st.session_state:

            # Text input for user confirmation
            user_confirmation = st.text_input("Have you completed the payment? Type 'success' or 'fail'.")

            # Calculate the elapsed time
            current_time = datetime.now()
            elapsed_time = current_time - st.session_state.payment_start_time
            time_limit = timedelta(minutes=5)  # 5 minutes limit

            # Check if within the time limit
            if elapsed_time < time_limit:
                if user_confirmation.lower() == "success":
                    notifier.order_new_notification(1, cntrNotify)

                    # User confirmed payment within time limit, proceed with order details
                    order_number = random.randint(100, 999)
                    prep_time = random.randint(10, 15)
                    st.session_state.order_number = order_number
                    st.session_state.prep_time = prep_time
                    st.session_state.total_price = total_price

                    # Deduct points only if the order is successful
                    points_to_use = st.session_state.points_to_use if 'points_to_use' in st.session_state else 0
                    if points_to_use > 0:
                        user_points = get_membership_points(username, POINTS)  # Fetch current points
                        if points_to_use <= user_points:  # Check if the user has enough points
                            user_points -= points_to_use  # Deduct the used points
                            update_membership_points(username, -points_to_use, POINTS)  # Deduct points in Excel
                            st.session_state.user_points = user_points  # Update session state with new points
                            st.success(f"Successfully applied {points_to_use} points. New balance: {user_points} points.")
                        else:
                            st.error("You cannot apply more points than you have.")
                    else:
                        st.success("No points applied.")
                    
                    # Add coffee orders to history
                    for coffee, details in coffee_orders.items():
                        milk_sugar_info = []
                        if details.get('milk', False):
                            milk_sugar_info.append("Milk")
                        elif details.get('noMilk', False):
                            milk_sugar_info.append("No Milk")
                        else:
                            milk_sugar_info.append("No Milk or Sugar Add-ons")  # Default if neither option selected

                    # Determine sugar options
                        if details.get('sugar', False):
                            milk_sugar_info.append("Extra Sugar")
                        elif details.get('noSugar', False):
                            milk_sugar_info.append("No Sugar")

                        # Combine info into a single text
                        milk_sugar_text = ", ".join(milk_sugar_info)

                        # Initialize remaining points discount to ensure consistency
                        remaining_points_discount = points_discount_amount

                        # Add coffee orders to history
                        for i, (coffee, details) in enumerate(coffee_orders.items()):
                            # Calculate the original price for this coffee order
                            coffee_price = (Decimal(coffee_menu[coffee]) * details['quantity'] +
                                            (Decimal(0.50) if details['size'] == "Medium" else 
                                            Decimal(1.00) if details['size'] == "Large" else Decimal(0)) * details['quantity'])
                            if details['sugar'] or details['milk']:
                                coffee_price += Decimal(0.25) * details['quantity']

                            # Calculate the promo discount for this coffee order
                            promo_discount_per_item = (promo_discount_percentage / Decimal(100)) * coffee_price
                            promo_discount_per_item = promo_discount_per_item.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

                            # Distribute points discount proportionally
                            points_discount_per_item = (remaining_points_discount / Decimal(total_items) * details['quantity']) if total_items > 0 else Decimal(0)
                            points_discount_per_item = points_discount_per_item.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                            
                            # Adjust remaining points discount for the last item
                            if i == len(coffee_orders) - 1:
                                points_discount_per_item += remaining_points_discount - points_discount_per_item * details['quantity']

                            # Calculate the discounted price for this coffee order
                            discounted_price = coffee_price - promo_discount_per_item - points_discount_per_item
                            discounted_price = discounted_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

                            # Deduct the distributed points discount
                            remaining_points_discount -= points_discount_per_item * details['quantity']

                            coffee_order_data = {
                                "Order Number": order_number,
                                "Item": f"{coffee} ({details['size']}, {details['temperature']}, {milk_sugar_text})",
                                "Quantity": details['quantity'],
                                "Price": discounted_price,
                                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "Username": st.session_state.username,
                                "Status": "Received"
                            }
                            st.session_state.order_history = pd.concat([st.session_state.order_history, pd.DataFrame([coffee_order_data])], ignore_index=True)

                        # Add food orders to history
                        for i, (food, details) in enumerate(food_orders.items()):
                            food_price = Decimal(food_menu[food]) * details['quantity']  # Calculate the original price for this food order

                            # Calculate the promo discount for this food order
                            promo_discount_per_item = (promo_discount_percentage / Decimal(100)) * food_price
                            promo_discount_per_item = promo_discount_per_item.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

                            # Distribute points discount proportionally
                            points_discount_per_item = (remaining_points_discount / Decimal(total_items) * details['quantity']) if total_items > 0 else Decimal(0)
                            points_discount_per_item = points_discount_per_item.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

                            # Adjust remaining points discount for the last item
                            if i == len(food_orders) - 1:
                                points_discount_per_item += remaining_points_discount - points_discount_per_item * details['quantity']

                            # Calculate the discounted price for this food order
                            discounted_price = food_price - promo_discount_per_item - points_discount_per_item
                            discounted_price = discounted_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

                            # Deduct the distributed points discount
                            remaining_points_discount -= points_discount_per_item * details['quantity']

                            food_order_data = {
                                "Order Number": order_number,
                                "Item": food,
                                "Quantity": details['quantity'],
                                "Price": discounted_price,
                                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "Username": st.session_state.username,
                                "Status": "Received"
                            }
                            st.session_state.order_history = pd.concat([st.session_state.order_history, pd.DataFrame([food_order_data])], ignore_index=True)

                        # Reduce inventory for each item
                        for coffee, details in coffee_orders.items():
                            reduce_inventory(coffee, details['quantity'], details['milk'], details['sugar'])
                        for food, details in food_orders.items():
                            reduce_inventory(food, details['quantity'])

                        # Save order history to CSV
                        save_order_history()

                    # Clear payment start time
                    del st.session_state.payment_start_time

                    # Move to order summary page
                    st.session_state.order_placed = True
                    st.rerun()

                elif user_confirmation.lower() == "fail":
                    notifier.order_new_notification(0, cntrNotify)
                    st.warning("Payment failed! Please try again in 5 seconds.")
                    time.sleep(5)
                    st.session_state.order_placed = False
                    # Clear payment start time
                    if "payment_start_time" in st.session_state:
                        del st.session_state.payment_start_time
                    st.rerun()

                elif user_confirmation:
                    # Handles invalid input, keeps the initial instructions visible
                    st.error("Invalid input entered. Please type 'success' or 'fail'.")
            else:
                # Time is up
                notifier.order_new_notification(0, cntrNotify)
                st.write("Exceeded the time limit! Please try again in 5 seconds.")
                time.sleep(5)
                st.session_state.order_placed = False
                # Clear payment start time
                if "payment_start_time" in st.session_state:
                    del st.session_state.payment_start_time
                st.rerun()
   
    else:
        if 'username' in st.session_state:
            # Load the unified order history CSV file
            filename = "all_users_order_history.csv"
            all_orders = pd.read_csv(filename)

            # Filter orders based on the logged-in user's username
            user_orders = all_orders[all_orders["Username"] == st.session_state.username]

            # Display the order history if it exists
            if not user_orders.empty:
                # Sort orders by "Time" to get the latest order
                user_orders["Time"] = pd.to_datetime(user_orders["Time"])

                # Get the latest order's number based on the most recent time
                latest_order = user_orders.sort_values("Time", ascending=False).iloc[0]
                latest_order_number = latest_order["Order Number"]

                # Filter orders with the same order number, and sort by "Status Priority" and "Time"
                # Define custom priority mapping for order statuses
                status_priority = {
                    "Completed": 3,
                    "Cancelled": 2,
                    "Processing": 1,
                    "Received": 0
                }

                # Add a new column to represent the status priority
                user_orders["Status Priority"] = user_orders["Status"].map(status_priority)

                # Filter the orders with the same "Order Number" as the latest one
                same_order_number = user_orders[user_orders["Order Number"] == latest_order_number]

                # Sort by "Status Priority" (highest priority first), then by "Time" (most recent first)
                latest_order = same_order_number.sort_values(by=["Status Priority", "Time"], ascending=[False, False]).iloc[0]

                # Get the latest order status and display it
                latest_order_status = latest_order["Status"]

                # Notify based on the status of the latest order
                if latest_order_status == "Completed":
                    notifier.order_ready_notification(latest_order_number, cntrNotify)
                elif latest_order_status == "Cancelled":
                    notifier.order_cancel_notification(latest_order_number, cntrNotify)

        # Process notifications first
        status = st.session_state.order_history.loc[st.session_state.order_history["Order Number"] == st.session_state.order_number, "Status"].values

        # Ensure we check the first value in the array if it exists
        if len(status) > 0:
            status = status[0]  # Get the first (and ideally only) value
        else:
            status = "Unknown"  # Default value if no match is found

        # Trigger appropriate notification
        if status == "Received":
            notifier.order_new_notification(1, cntrNotify)
        elif status == "Processing":
            notifier.order_processing_notification(cntrNotify)
        elif status == "Completed":
            notifier.order_ready_notification(order_number, cntrNotify)
        elif status == "Cancelled":
            notifier.order_cancel_notification(order_number, cntrNotify)

        st.markdown("<h2 style='text-align: center; font-size: 60px; color: white;'>Order Invoice</h2>", unsafe_allow_html=True)
        st.markdown(f"Order Number: <span style='color: orange; font-weight: bold;'>{st.session_state.order_number}</span>", unsafe_allow_html=True)
        st.markdown(f"Total Price (RM):  <span style='color: orange; font-weight: bold;'>{st.session_state.total_price:.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"Estimated Preparation Time (mins): <span style='color: orange; font-weight: bold;'>{st.session_state.prep_time}</span> ", unsafe_allow_html=True)

        st.markdown("<div class='subheading'>Order Details: </div>", unsafe_allow_html=True)
        st.dataframe(st.session_state.order_history[st.session_state.order_history["Order Number"] == st.session_state.order_number])

        # Display the extra request
        extra_request = st.session_state.extra_request if "extra_request" in st.session_state else "None"
        st.markdown("<div class='subheading'>Extra Requests:</div>", unsafe_allow_html=True)
        st.write(f"<span style='color: orange; font-weight: bold;'>{extra_request}</span>",unsafe_allow_html=True)

        # Add download button for the PDF receipt
        pdf_buffer = generate_pdf_receipt(st.session_state.order_number, st.session_state.total_price)
        st.download_button(
            label="Download Receipt",
            data=pdf_buffer,
            file_name=f"{st.session_state.order_number}_Receipt.pdf",
            mime="application/pdf",
        )

        if st.button("Place Another Order"):
            st.session_state.order_placed = False
            st.rerun()

 

# ------------------ Admin Order Management ------------------ #
def admin_order_management(EXCEL_FILE):
    st.markdown(
        """
        <h1 style="text-align: center;">Manage Customer Orders</h1>
        <br>
        """,
        unsafe_allow_html=True
    )

    # Initialize NotifyStaff instance
    notifier = NotifyStaff()
    cntrNotify = st.container()
    
    # Check if there are any orders
    if not st.session_state.order_history.empty:
        # Group orders by order number so that food and beverages are combined under each order
        grouped_orders = st.session_state.order_history.groupby("Order Number")
        
        # Display each grouped order
        for order_number, group in grouped_orders:
            st.markdown(f"### Order Number: {order_number}")

            # Retrieve the username associated with the order
            order_username = group["Username"].iloc[0]
            
            # Display each item in the order (food and beverages together)
            for index, row in group.iterrows():
                item = row["Item"]
                quantity = row["Quantity"]
                price = row["Price"]
                status = row["Status"]
                
                # Display item details
                st.markdown(f"- **Item:** {item} | **Quantity:** {quantity} | **Price:** RM {price:.2f}")
            
            # Display current order status
            current_status = group["Status"].iloc[0]  # Assumes all items in an order share the same status
            st.markdown(f"**Current Status:** {current_status}")
            
            # Create buttons for status updates
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Processing", key=f"processing_{order_number}_{index}"):
                    update_order_status(order_number, "Processing")
                    notifier.order_processing_notification(order_number, cntrNotify)
            with col2:
                if st.button("Completed", key=f"completed_{order_number}_{index}"):
                    update_order_status(order_number, "Completed")
                    update_membership_points(order_username, 10, EXCEL_FILE)
                    notifier.order_complete_notification(order_number, cntrNotify)
            with col3:
                if st.button("Cancel", key=f"cancelled_{order_number}_{index}"):
                    notifier.order_cancel_notification(order_number, cntrNotify)
                    update_order_status(order_number, "Cancelled")
            
            st.markdown("---")  # Add a divider between orders

        # Filter out completed or canceled orders for display
        st.session_state.order_history = st.session_state.order_history[~st.session_state.order_history["Status"].isin(["Completed", "Cancelled"])]

    else:
        st.write("No orders have been placed yet.")

# Function to update the order status
def update_order_status(order_number, new_status):
    # Update the status in the order history DataFrame for all items with the same order number
    st.session_state.order_history.loc[st.session_state.order_history["Order Number"] == order_number, "Status"] = new_status
    
    # Save updated order history to CSV
    save_order_history()
    
    # Provide feedback
    st.success(f"Order Number {order_number} has been updated to '{new_status}'.")



# ------------------ Admin view order history ------------------ #
def admin_order_history():
    # Initialize NotifyStaff instance
    notifier = NotifyStaff()
    cntrNotify = st.container()

    # Display header
    st.title("Order Status")
    st.markdown("<div class='subheading' style='font-size: 20px;  color: orange; margin-top: 20px;'>Received Orders</div>", unsafe_allow_html=True)
    
    # Process notifications first
    if not st.session_state.order_history.empty:
        for index, row in st.session_state.order_history.iterrows():
            order_id = row["Order Number"]
            status = row["Status"]
            
            # Trigger appropriate notification
            if status == "Received":
                notifier.new_order_notification(order_id, cntrNotify)
            elif status == "Processing":
                notifier.order_processing_notification(order_id, cntrNotify)
        
        # After showing notifications, display the order table
        st.dataframe(st.session_state.order_history)
    else:
        # Display "no orders left" if the order history is empty
        st.write("No orders have been placed yet.")

    # View Order History by Order Number
    st.markdown("<div class='subheading' style='font-size: 20px;  color: orange; margin-top: 20px;'>Search Order</div>", unsafe_allow_html=True)
    search_order = st.text_input("Enter Order Number", key="search_order")

    if search_order:
        try:
            search_order = int(search_order)
            searched_order = st.session_state.order_history[st.session_state.order_history["Order Number"] == search_order]
            if not searched_order.empty:
                st.dataframe(searched_order)
            else:
                st.write(f"No order found with Order Number {search_order}.")
        except ValueError:
            st.error("Please enter a valid Order Number.")

# ------------------ Inventory management ------------------ #
def inventory_management():

    st.markdown(
        """
        <h1 style="text-align: center;">Inventory Management</h1>
        <br>
        """,
        unsafe_allow_html=True
    )
    
    # Initialize NotifyStaff instance
    notifier = NotifyStaff()
    cntrNotify = st.container()
    st.markdown("<div class='subheading' style='font-size: 20px;  color: orange; margin-top: 20px;'>Inventory Status</div>", unsafe_allow_html=True)
    inventory_data = {item: max(0, quantity) for item, quantity in st.session_state.inventory.items()}
    st.table(pd.DataFrame(list(inventory_data.items()), columns=["Item", "Quantity"]))

    # Low Inventory Alerts
    low_inventory_items = restock_list()
    if low_inventory_items:
        notifier.limited_inventory_notification(cntrNotify)
        st.warning(f"Low Inventory Alert: Please restock the following items - {', '.join(low_inventory_items)}")


    # Manual Restocking
    with st.expander("Restock Inventory"):
        restock_coffee_beans = st.number_input("Restock Coffee Beans (g)", min_value=0, step=100)
        restock_milk = st.number_input("Restock Milk (ml)", min_value=0, step=50)
        restock_sugar = st.number_input("Restock Sugar (g)", min_value=0, step=50)
        restock_cups = st.number_input("Restock Cups", min_value=0, step=10)
        restock_bread = st.number_input("Restock Bread (g)", min_value=0, step=50)
        restock_pasta = st.number_input("Restock Pasta (g)", min_value=0, step=50)
        restock_eggs = st.number_input("Restock Eggs", min_value=0, step=5)
        restock_cheese = st.number_input("Restock Cheese (g)", min_value=0, step=50)
        restock_lettuce = st.number_input("Restock Lettuce (g)", min_value=0, step=50)
        restock_tomatoes = st.number_input("Restock Tomatoes (g)", min_value=0, step=50)
        restock_pasta_sauce = st.number_input("Restock Pasta Sauce (ml)", min_value=0, step=50)
        restock_pastry_sheets = st.number_input("Restock Pastry Sheets", min_value=0, step=5)
        restock_condensed_milk = st.number_input("Restock Condensed Milk (ml)", min_value=0, step=50)

    if st.button("Update Inventory"):
        st.session_state.inventory["Coffee Beans (g)"] = max(0, st.session_state.inventory["Coffee Beans (g)"] + restock_coffee_beans)
        st.session_state.inventory["Milk (ml)"] = max(0, st.session_state.inventory["Milk (ml)"] + restock_milk)
        st.session_state.inventory["Sugar (g)"] = max(0, st.session_state.inventory["Sugar (g)"] + restock_sugar)
        st.session_state.inventory["Cups"] = max(0, st.session_state.inventory["Cups"] + restock_cups)
        st.session_state.inventory["Bread (g)"] = max(0, st.session_state.inventory["Bread (g)"] + restock_bread)
        st.session_state.inventory["Pasta (g)"] = max(0, st.session_state.inventory["Pasta (g)"] + restock_pasta)
        st.session_state.inventory["Eggs"] = max(0, st.session_state.inventory["Eggs"] + restock_eggs)
        st.session_state.inventory["Cheese (g)"] = max(0, st.session_state.inventory["Cheese (g)"] + restock_cheese)
        st.session_state.inventory["Lettuce (g)"] = max(0, st.session_state.inventory["Lettuce (g)"] + restock_lettuce)
        st.session_state.inventory["Tomatoes (g)"] = max(0, st.session_state.inventory["Tomatoes (g)"] + restock_tomatoes)
        st.session_state.inventory["Pasta Sauce (ml)"] = max(0, st.session_state.inventory["Pasta Sauce (ml)"] + restock_pasta_sauce)
        st.session_state.inventory["Pastry Sheets"] = max(0, st.session_state.inventory["Pastry Sheets"] + restock_pastry_sheets)
        st.session_state.inventory["Condensed Milk (ml)"] = max(0, st.session_state.inventory["Condensed Milk (ml)"] + restock_condensed_milk)
        
        st.success("Inventory Updated Successfully!")                                    