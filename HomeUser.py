import streamlit as st
from PIL import Image

def user_home():
    # Welcome message
    st.subheader("A Perfect Blend of Premium Coffee and Innovation")
    st.markdown(
        """
        <div style="text-align: justify">
            Twilight Coffee Shop is your home away from home, offering an immersive dining experience that 
            combines technology and the art of coffee-making. Explore our rich, premium blends while staying 
            connected to a world of modern convenience.
        </div>
        <br><br>
        """,
        unsafe_allow_html=True
    )

    # Banner paths
    banner_images = [
        "resource/banner1.jpg",
        "resource/banner2.jpg",
        "resource/banner3.jpg",
        "resource/banner4.jpg"
    ]

    # Initialize session state for current image index
    if "banner_index" not in st.session_state:
        st.session_state.banner_index = 0  # Start with the first image

    # Create a container for the banner and buttons
    with st.container():
        # Display the current banner image
        current_image_path = banner_images[st.session_state.banner_index]
        img = Image.open(current_image_path)
        st.image(img, use_column_width=True)

        # Buttons for manual banner control
        col1, col2, col3 = st.columns([2, 4, 1])
        with col1:
            if st.button("⬅️ Previous", key="prev"):
                st.session_state.banner_index = (st.session_state.banner_index - 1) % len(banner_images)
        with col3:
            if st.button("Next ➡️", key="next"):
                st.session_state.banner_index = (st.session_state.banner_index + 1) % len(banner_images)

    st.markdown("---")

    # Additional content that loads immediately
    with st.container():
        st.write("### What Makes Us Special")
        st.image("resource/interior.jpg", caption="A cozy environment to enjoy coffee", use_column_width=True)

        st.write(
            """
            - **Premium Coffee**: Sourced from the finest beans around the world.
            - **Innovative Dining**: A seamless blend of technology and service.
            - **Community Space**: Your go-to spot for meetings, work, or relaxation.
            """
        )

        st.markdown("---")
        st.write("### Customer Favorites")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.image("resource/pasta.jpg", caption="Pasta", use_column_width=True)
            st.write("Rich and creamy, our signature dish.")

        with col2:
            st.image("resource/caramelMacchiato.jpg", caption="Caramel Macchiato", use_column_width=True)
            st.write("A sweet, velvety coffee. Available Hot/Cold.")

        with col3:
            st.image("resource/eggTart.jpg", caption="Egg Tart", use_column_width=True)
            st.write("A classic favorite baked fresh daily.")

        st.markdown("---")
        st.write("### Visit Us Today!")
        st.write(
            """
            Located in the heart of the city, Twilight Coffee Shop offers a unique 
            blend of flavors and ambiance. Come and experience the best coffee in town!
            """
        )
