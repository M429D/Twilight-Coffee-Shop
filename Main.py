import streamlit as st
import pandas as pd
import hashlib
from HomeUser import user_home
from Menu import display_menu
from Notify import NotifyCustomer
from Order import take_order, display_user_order_history, admin_order_history, inventory_management, admin_order_management
from HomeAdmin import admin_home
from admin_promo import promo_code_management, initialize_and_load_promotions
from SalesReporting import sales_reporting
from AnalyticDashboard import analytics_dashboard
from PIL import Image
import time
import json
from datetime import datetime

# Constants
EXCEL_FILE = 'TWILIGHT_USERS.xlsx'
ADMIN_USERNAME = 'admin'  # Define admin username
ADMIN_PASSWORD = 'admin321'  # Define admin password
LOCAL_ICON_PATH = 'resource/TwilightIcon.ico'

# Initialize Excel file
def init_excel():
    try:
        pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=['First Name', 'Last Name', 'Email', 'Contact Number', 'Username', 'Password'])
        df.to_excel(EXCEL_FILE, index=False)

# ------------------ Initialize Global Variables ------------------ #
if 'order_history' not in st.session_state:
    st.session_state.order_history = pd.DataFrame(columns=['Order Number', 'Item', 'Quantity', 'Price', 'Time'])
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

# Hash the password for secure storage
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Verify user login credentials
def verify_user(username, password):
    hashed_password = hash_password(password)
    
    # Check for admin credentials
    if username == ADMIN_USERNAME and hashed_password == hash_password(ADMIN_PASSWORD):
        return 'Admin', True  # Return 'Admin' and admin status as True

    # Check for regular users
    df = pd.read_excel(EXCEL_FILE)
    user = df[(df['Username'] == username) & (df['Password'] == hashed_password)]

    if not user.empty:
        return user.iloc[0]['First Name'], False
    else:
        return None, False

# Add a new user to Excel
def add_user(first_name, last_name, email, contact_number, username, password, membership_points=0):
    df = pd.read_excel(EXCEL_FILE)
    hashed_password = hash_password(password)

    # Convert contact number to integer if possible
    try:
        contact_number = int(contact_number)
    except ValueError:
        st.error("Please enter a valid contact number.")

    new_user = pd.DataFrame({
        'First Name': [first_name],
        'Last Name': [last_name],
        'Email': [email],
        'Contact Number': [contact_number],
        'Username': [username],
        'Password': [hashed_password],
        'Membership Points': [membership_points]
    })
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)

# Main app function
def main():
    # Load promotions into session state
    initialize_and_load_promotions()  # Call the function to load promotions
    
    # Get the payment status from URL query parameters
    payment_status = st.query_params.get("payment", [""])  # 'success' or 'fail'

    # Check payment status
    if payment_status == "fail":
        st.error("Payment failed. Please try again or contact support.")
    
        countdown_placeholder = st.empty()  # Create a placeholder for the countdown
        countdown_time = 7  # Start countdown from 7 seconds

        # Countdown loop
        for i in range(countdown_time, 0, -1):
            countdown_placeholder.write(f"Redirecting user back to the login page in {i} seconds...")
            time.sleep(1)  # Sleep for 1 second

        # After countdown, redirect the user using a meta refresh
        countdown_placeholder.write("<meta http-equiv='refresh' content='0; url=http://localhost:8501/'>", unsafe_allow_html=True)
    
    # Set up page navigation using session state
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Login'

    # Ensure 'first_name', 'logged_in', and 'is_admin' keys are initialized
    if 'first_name' not in st.session_state:
        st.session_state['first_name'] = ''
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'is_admin' not in st.session_state:
        st.session_state['is_admin'] = False

    # Page navigation logic
    page = st.session_state['page']

    if page == "Login":
        set_page_config("Login App", "🔐")
        login_page()
    elif page == "Sign Up":
        set_page_config("Sign Up", "✍️")
        sign_up_page()
    elif page == "Home":
        set_page_config("TWILIGHT CS", LOCAL_ICON_PATH)
        home_page()
    elif page == "Admin Dashboard":
        set_page_config("Admin Dashboard", "📊")
        admin_dashboard()
    elif page == "Feedback":
        feedback_page()

# Function to set the page title and icon
def set_page_config(title, icon):
    st.set_page_config(page_title=title, page_icon=icon)

# Login page
def login_page():
    # Center-align the logo using Streamlit columns
    col1, col2, col3 = st.columns([2, 1, 2])  # Create three columns

    with col2:  # Center column
        st.image("Resource/LOGO PNG.png", width=150)  # Display the logo

    st.title("Log In")

    # Username and password inputs
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # Add space between the password field and the login button
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)

    # Login button with wider style
    if st.button("Login", key="login_button", help="Click to log in", use_container_width=True):
        first_name, is_admin = verify_user(username, password)
        if first_name:
            st.success("Login successful!")
            st.session_state['logged_in'] = True
            st.session_state['first_name'] = first_name  # Set the first name in session state
            st.session_state['username'] = username
            st.session_state['is_admin'] = is_admin
            
            # Redirect based on user type
            if is_admin:
                st.session_state['page'] = "Admin Dashboard"
            else:
                st.session_state['page'] = "Home"
            
            st.rerun()  # Redirect to the appropriate page
        else:
            st.error("Invalid Username or Password.")

    # Styled separator line
    st.markdown("<hr style='border: 1px solid #ccc; margin: 20px 0;'>", 
                unsafe_allow_html=True)

    # "Don't have an account?" text and "Go to Sign Up" button
    st.write("Don't have an account?")

    # Add space between the text and the go to sign up button
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    if st.button("Go to Sign Up", key="signup_button", use_container_width=True):
        st.session_state['page'] = "Sign Up"
        st.rerun()  # Redirect to the Sign Up page

# Sign-up page
def sign_up_page():
    # Initialize NotifyStaff instance
    notifier = NotifyCustomer()
    cntrNotify = st.container()

    st.title("Sign Up")

    # Sign-up form inputs
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")
    contact_number = st.text_input("Contact Number")  # Added contact number field
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    confirm_password = st.text_input("Confirm Password", type='password')

    # Add space between the confirm password field and the sign up button
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)

    # Sign Up button with wider style
    if st.button("Sign Up", use_container_width=True):
        if password != confirm_password:
            notifier.register_notification(0, cntrNotify)
            st.error("Passwords do not match.")
        elif not all([first_name, last_name, email, contact_number, username]):
            notifier.register_notification(0, cntrNotify)
            st.error("Please fill all fields correctly.")
        else:
            notifier.register_notification(1, cntrNotify)
            add_user(first_name, last_name, email, contact_number, username, password)
            st.success("Account created successfully!")
            st.info("Go to Login page to log in.")
            st.session_state['page'] = "Login"
            st.rerun()  # Redirect to the Login page

# Save customer feedback to a JSON file
def save_feedback_to_json_file(filename, feedback):
    # Check if the file exists and is not empty
    try:
        with open(filename, 'r') as f:
            feedback_list = json.load(f)  # Load the existing feedback data
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_list = []  # If file doesn't exist or is empty, start a new list
    
    # Append the new feedback to the list
    feedback_list.append(feedback)
    
    # Save the updated list back to the file
    with open(filename, 'w') as f:
        json.dump(feedback_list, f, indent=4)  # Save the list as formatted JSON

def feedback_page():
    st.title("Customer Feedback Session")

    # Add a humanized introductory message
    st.write("Wait a minute! We’d love your feedback on how we’re doing to make your next visit even better! 😊")

    # Collecting feedback with more humanized prompts
    food_quality_rating = st.slider("How would you rate the quality of our food and beverages?", 1, 5, 3, help="1 = Poor, 5 = Excellent")
    service_rating = st.slider("How satisfied were you with our customer service?", 1, 5, 3, help="1 = Not Satisfied, 5 = Very Satisfied")
    uiux_rating = st.slider("How would you rate the website’s user interface and experience?", 1, 5, 3, help="1 = Poor, 5 = Excellent")
    additional_comments = st.text_area("Any additional thoughts or suggestions? (Optional)")

    if st.button("Submit Feedback"):
        feedback = {
            'food_quality_rating': food_quality_rating,
            'service_rating': service_rating,
            'uiux_rating': uiux_rating,
            'comments': additional_comments,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_feedback_to_json_file('customer_feedback.json', feedback)
        
        # Display a thank-you popup message
        st.balloons()
        st.success("Thank you for your valuable feedback! We sincerely appreciate it and look forward to serving you better in the future.")
        time.sleep(5)
        # Redirecting to the login page
        st.session_state['logged_in'] = False
        st.session_state['first_name'] = ''
        st.session_state['page'] = 'Login'
        st.rerun()

# Home page for regular users
def home_page():
    if st.session_state['logged_in'] and not st.session_state['is_admin']:

        # Sidebar navigation
        st.sidebar.image("Resource/LOGO PNG.png", width=100)
        st.sidebar.title("More Exploration")
        
        # Sidebar options
        page_options = ["Home", "Menu", "Order", "Purchased History", "About"]
        selected_page = st.sidebar.radio("Navigate", page_options)

        # Page content based on the selected option
        if selected_page == "Home":
            st.markdown(
                """
                <h1 style="text-align: center;">Welcome to Twilight Coffee Shop</h1>
                <br>
                """,
                unsafe_allow_html=True
            )
            first_name = st.session_state.get('first_name', '')
            st.header(f"Hello, {first_name} 😉!")
            user_home()

        elif selected_page == "Menu":
            display_menu()

        elif selected_page == "Order":
            take_order()

        elif selected_page=="Purchased History":
            display_user_order_history(EXCEL_FILE)

        elif selected_page=="About":
            # Set the page title
            st.markdown(
                """
                <h1 style="text-align: center;">About Us</h1>
                <br>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                """
                <br>
                <div style="text-align: justify; font-style: italic; font-weight: bold;">
                    Welcome to our team page! Here you can meet the talented individuals who make up our leadership team. Each of us is dedicated to achieving our company's goals and driving innovation in our respective roles.
                </div>
                <br><br>
                """,
                unsafe_allow_html=True
            )

            # Define team members with name, ID, and role
            team_members = [
                {"name": "Muhammad bin Hassan Ghani", "id": "20001468", "role": "Chief Executive Officer (CEO)", "photo": "resource/Muhd.jpg"},
                {"name": "Harivarma Subramaniam", "id": "20001506", "role": "Chief Technical Officer (CTO)", "photo": "resource/Hari.jpg"},
                {"name": "Angeline Chong Vun Yiing", "id": "21000941", "role": "Chief Finance Officer (CFO)", "photo": "resource/Ang.jpg"},
                {"name": "Loh Jia Yi", "id": "21001052", "role": "Chief Marketing Officer (CMO)", "photo": "resource/JiaYi.jpg"},
                {"name": "Amalin Liyana", "id": "20001473", "role": "Chief Operating Officer (COO)", "photo": "resource/Amalin.jpg"},
            ]

            # Set the fixed height for the images
            image_height = 200

            # Display the first row
            cols_middle_1 = st.columns([6, 1, 6, 1, 6])
            with cols_middle_1[0]:
                member = team_members[0]
                image = Image.open(member["photo"])
                image = image.resize((int(image_height * image.width / image.height), image_height))  # Maintain aspect ratio
                st.image(image, use_column_width=False)
                st.markdown(f"### {member['name']}")
                st.markdown(f"**ID:** {member['id']}")
                st.markdown(f"**Role:** {member['role']}")

            with cols_middle_1[2]:
                member = team_members[1]
                image = Image.open(member["photo"])
                image = image.resize((int(image_height * image.width / image.height), image_height))  # Maintain aspect ratio
                st.image(image, use_column_width=False)
                st.markdown(f"### {member['name']}")
                st.markdown(f"**ID:** {member['id']}")
                st.markdown(f"**Role:** {member['role']}")

            with cols_middle_1[4]:
                member = team_members[2]
                image = Image.open(member["photo"])
                image = image.resize((int(image_height * image.width / image.height), image_height))  # Maintain aspect ratio
                st.image(image, use_column_width=False)
                st.markdown(f"### {member['name']}")
                st.markdown(f"**ID:** {member['id']}")
                st.markdown(f"**Role:** {member['role']}")

            # Display the second row
            cols_middle_1 = st.columns([2, 6, 2, 6, 2])
            with cols_middle_1[1]:
                member = team_members[3]
                image = Image.open(member["photo"])
                image = image.resize((int(image_height * image.width / image.height), image_height))  # Maintain aspect ratio
                st.image(image, use_column_width=False)
                st.markdown(f"### {member['name']}")
                st.markdown(f"**ID:** {member['id']}")
                st.markdown(f"**Role:** {member['role']}")

            with cols_middle_1[3]:
                member = team_members[4]
                image = Image.open(member["photo"])
                image = image.resize((int(image_height * image.width / image.height), image_height))  # Maintain aspect ratio
                st.image(image, use_column_width=False)
                st.markdown(f"### {member['name']}")
                st.markdown(f"**ID:** {member['id']}")
                st.markdown(f"**Role:** {member['role']}")

        # Add empty space in the sidebar before the logout button
        st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)

        # Add the logout button at the bottom of the sidebar
        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state['page'] = 'Feedback'  # Set page to 'Feedback'
            st.rerun()

    else:
        st.warning("You need to log in first.")
        st.session_state['page'] = "Login"
        st.rerun()  # Redirect to the Login page

# Admin dashboard page
def admin_dashboard():
    if st.session_state['logged_in'] and st.session_state['is_admin']:

        # Sidebar navigation
        st.sidebar.image("resource/LOGO PNG.png", width=100)
        st.sidebar.title("More Exploration")
        
        # Sidebar options
        page_options = ["Home", "User Overview", "Customer Orders", "Inventory Management","Promo Code Management", "Sales Reporting", "Analytics Dashboard"]
        selected_page = st.sidebar.radio("Navigate", page_options)

        # Page content based on the selected option
        if selected_page == "Home":
            st.markdown(
                """
                <h1 style="text-align: center;">Welcome to Twilight Coffee Shop Admin Dashboard</h1>
                <br>
                """,
                unsafe_allow_html=True
            )
            st.write("Welcome, Admin 😉!")
            admin_home()

        elif selected_page == "User Overview":
            st.markdown(
                """
                <h1 style="text-align: center;">👥 User Activity</h1>
                <br>
                """,
                unsafe_allow_html=True
            )
        
            st.markdown("## System Management:")
            df = pd.read_excel(EXCEL_FILE)
            st.dataframe(df)

            st.markdown("## System Overview:")
            st.markdown(f"#### Number of registered users: {len(df)}")

        elif selected_page=="Customer Orders":
            admin_order_management(EXCEL_FILE)

        elif selected_page == "Inventory Management":
            inventory_management()

        elif selected_page == "Promo Code Management":
            promo_code_management()   
          
        elif selected_page == "Sales Reporting":
            sales_reporting('all_users_order_history.csv')

        elif selected_page == "Analytics Dashboard":
            analytics_dashboard()

        # Add empty space in the sidebar before the logout button
        st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)

        # Add the logout button at the bottom of the sidebar
        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state['logged_in'] = False
            st.session_state['first_name'] = ''
            st.session_state['page'] = 'Login'
            st.rerun()  # Redirect to the Login page
    
    else:
        st.warning("Unauthorized access.")
        st.session_state['page'] = "Login"
        st.rerun()  # Redirect to the Login page

# Initialize Excel file
init_excel()

if __name__ == "__main__":
    main()
