import streamlit as st

def display_menu():
    st.markdown("""
        <h1 style='text-align: center; color: #6F4C3E; font-family: "Arial", sans-serif; font-size: 70px; margin: 0;'>
            TWILIGHT COFFEE SHOP
        </h1>
    """, unsafe_allow_html=True)

    # Add a gap below the shop name
    st.markdown("<br>", unsafe_allow_html=True)

    # Display the menu header
    st.markdown("<h2 style='text-align: center; font-size: 60px; color: white;'>Menu</h2>", unsafe_allow_html=True)

    # Adding a gap
    st.markdown("<br>", unsafe_allow_html=True)


    # Menu items with images
    beverages = {
        "Americano": ("RM 11.00", "resource/americano.png"),
        "Cappuccino": ("RM 12.00", "resource/cappucino.jpg"),
        "Latte": ("RM 12.00", "resource/latte.jpg"),
        "Caramel Macchiato": ("RM 14.00", "resource/caramelMacchiato.jpg")
    }

    food_items = {
        "Sandwich": ("RM 11.00", "resource/sandwich.jpg"),
        "Pasta": ("RM 14.00", "resource/pasta.jpg"),
        "Egg Tart":("RM 6.00", "resource/eggTart.jpg")
    }

    # Section: Food
    st.markdown("<div class='subheading' style='font-size: 40px; color: gold;'>Food</div>", unsafe_allow_html=True)
    food_cols = st.columns(4)  # Create four columns for food items
    

    for i, (item, (price, image_url)) in enumerate(food_items.items()):
        with food_cols[i % 4]:
            st.image(image_url, width=150)  # Show the image
            st.markdown(f"<strong>{item}</strong><br>{price}", unsafe_allow_html=True)  # Show caption

    # Adding a gap
    st.markdown("<br>", unsafe_allow_html=True)

    # Section: Beverages
    st.markdown("<div class='subheading' style='font-size: 40px;  color: gold; margin-top: 30px;'>Beverages</div>", unsafe_allow_html=True)
    beverage_cols = st.columns(4)  # Create four columns for beverages

    for i, (item, (price, image_url)) in enumerate(beverages.items()):
        with beverage_cols[i % 4]:  # Alternate between columns
            st.image(image_url, width=150)
            st.markdown(f"<strong>{item}</strong><br>{price}<br><em>Hot / Cold</em>", unsafe_allow_html=True)
    
    

    