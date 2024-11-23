import streamlit as st
import pandas as pd

PROMO_CODES_FILE = 'TWILIGHT_PROMO_CODES.xlsx'

# Initialize promo codes Excel file
def init_promo_codes_excel():
    try:
        pd.read_excel(PROMO_CODES_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=['Promo Code', 'Description', 'Discount Percentage (%)', 'Min Purchase', 'Starting Date', 'Expiration Date'])
        df.to_excel(PROMO_CODES_FILE, index=False)

def load_promotions_from_excel():
    df = pd.read_excel(PROMO_CODES_FILE)
    promotions_dict = df.set_index('Promo Code').T.to_dict()
    return promotions_dict

def save_promotions_to_excel():
    df = pd.DataFrame.from_dict(st.session_state.promotions, orient='index')
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Promo Code'}, inplace=True)
    df.to_excel(PROMO_CODES_FILE, index=False)

def initialize_and_load_promotions():
    # Initialize promo codes from Excel
    init_promo_codes_excel()

    # Load existing promotions into session state
    if 'promotions' not in st.session_state:
        st.session_state.promotions = load_promotions_from_excel()

def promo_code_management():
    initialize_and_load_promotions()

    # ------------------ Discount/Promo Management ------------------ #
    st.markdown(
        """
        <h1 style="text-align: center;">Manage Discounts & Promotions</h1>
        <br>
        """,
        unsafe_allow_html=True
    )

    # Dropdown to select between adding, editing, or deleting a promotion
    action = st.selectbox("Select Action", ["Add Promotion", "Edit Promotion", "Delete Promotion"])

    # Form for adding promotion
    if action == "Add Promotion":
        with st.form("add_promo_form"):
            promo_code = st.text_input("Enter Promotion Code")
            promo_description = st.text_input("Description (e.g., '10% off orders over RM50')")

            discount_percentage = st.number_input("Discount Percentage (%)", min_value=1, max_value=100, step=1)

            min_purchase = st.number_input("Minimum Purchase Required (RM)", min_value=0.0)
            start_date = st.date_input("Starting Date")
            expiration_date = st.date_input("Expiration Date")

            submit_promo = st.form_submit_button("Add Promotion")

            if submit_promo:
                # Add promo to session state
                st.session_state.promotions[promo_code] = {
                    "Description": promo_description,
                    "Discount Percentage (%)": discount_percentage,
                    "Min Purchase": min_purchase,
                    "Starting Date": start_date,
                    "Expiration Date": expiration_date,
                }
                st.success(f"Promotion '{promo_code}' added successfully!")
                # Save to Excel
                save_promotions_to_excel()

    # Form for editing promotion
    elif action == "Edit Promotion":
        promo_code_to_edit = st.selectbox("Select Promotion Code to Edit", list(st.session_state.promotions.keys()))
        
        if promo_code_to_edit:
            details = st.session_state.promotions[promo_code_to_edit]

            with st.form("edit_promo_form"):
                # Populate fields with the selected promo code's details
                promo_description = st.text_input("Description", value=details.get('Description', ''))
                
                discount_percentage = st.number_input("Discount Percentage (%)", min_value=1, max_value=100, value=int(details.get('Discount Percentage (%)', 0)), step=1)

                min_purchase = st.number_input("Minimum Purchase Required (RM)", min_value=0.0, value=float(details.get('Min Purchase', 0)))
                
                # Convert date strings to datetime.date for the date input
                start_date = pd.to_datetime(details.get('Starting Date', '2023-01-01')).date()
                expiration_date = pd.to_datetime(details.get('Expiration Date', '2023-01-01')).date()

                # Set the date input fields
                start_date_input = st.date_input("Starting Date", value=start_date)
                expiration_date_input = st.date_input("Expiration Date", value=expiration_date)

                submit_edit = st.form_submit_button("Update Promotion")
                if submit_edit:
                    # Update the promotion in session state
                    st.session_state.promotions[promo_code_to_edit] = {
                        "Description": promo_description,
                        "Discount Percentage (%)": discount_percentage,
                        "Min Purchase": min_purchase,
                        "Starting Date": start_date_input,
                        "Expiration Date": expiration_date_input,
                    }
                    st.success(f"Promotion '{promo_code_to_edit}' updated successfully!")
                    # Save to Excel
                    save_promotions_to_excel()

    # Form for deleting promotion
    elif action == "Delete Promotion":
        promo_codes_to_delete = st.multiselect("Select Promotion Codes to Delete", list(st.session_state.promotions.keys()))
        if st.button("Delete Selected Promotions"):
            for code in promo_codes_to_delete:
                if code in st.session_state.promotions:
                    del st.session_state.promotions[code]
            st.success("Selected promotions deleted successfully.")
            # Save updated promotions to Excel
            save_promotions_to_excel()

    # Display current promotions in a DataFrame
    if st.session_state.promotions:
        st.markdown("### Current Promotions")
        promotions_df = pd.DataFrame.from_dict(st.session_state.promotions, orient='index').reset_index()
        promotions_df.columns = ['Promo Code', 'Description', 'Discount Percentage (%)', 'Min Purchase', 'Starting Date', 'Expiration Date']
        
        # Convert date columns to string format
        promotions_df['Starting Date'] = promotions_df['Starting Date'].astype(str)
        promotions_df['Expiration Date'] = promotions_df['Expiration Date'].astype(str)

        # Display the DataFrame using Streamlit's built-in function
        st.dataframe(promotions_df.style.set_table_attributes('style="white-space: nowrap;"'))

    else:
        st.write("No current promotions available.")