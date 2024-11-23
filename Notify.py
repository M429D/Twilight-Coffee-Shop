import random
import streamlit as st
from datetime import datetime

# ------------------ Notification Class for Consumer ------------------ #
class NotifyCustomer:

    def promo_notification(self, container):
        # Display a randomized daily promotion notification for consumers
        promo = random.choice(self.promotions)
        with container:
            st.success(f"🎉 Today's Promotion: {promo}")

    def order_new_notification(self, order_status, container):
        # Accept 1 for success and 0 for failure
        with container:
            if order_status == 1:
                st.success("✅ Your order was successful!")
            elif order_status == 0:
                st.error("❌ Your order has failed. Please try again.")
    
    def order_processing_notification(self, order_id, container):
        # Notify consumer that the order has been processed
        with container:
            st.info(f"⏳ Your order is being prepared by our barista!")

    def order_ready_notification(self, order_id, container):
        # Notify consumer that their order is ready for pickup
        with container:
            st.info(f"☕ Your order {order_id} is ready for pickup! Please proceed to the counter.")

    def order_cancel_notification(self, order_id, container):
        # Notify consumer that the order has been canceled
        with container:
            st.error(f"🚫 Order {order_id} has been canceled.")

    def register_notification(self, registration_status, container):
        # Notify user about registration status
        # Accept 1 for success and 0 for failure
        with container:
            if registration_status == 1:
                st.success("🎉 You have successfully registered your account!")
            elif registration_status == 0:
                st.error("❌ Registration failed. Please try again.")


# ------------------ Notification Class for Staff ------------------ #
class NotifyStaff:
    def new_order_notification(self, order_id, container):
        # Notify staff of a new order
        with container:
            st.info(f"📦 New Order Received! Order ID: {order_id}")

    def order_processing_notification(self, order_id, container):
        # Notify consumer that the order has been processed
        with container:
            st.info(f"⏳ Order {order_id} is being prepared")

    def order_complete_notification(self, order_id, container):
        # Notify consumer that the order has been completed
        with container:
            st.success(f"💯 Order {order_id} completed")

    def order_cancel_notification(self, order_id, container):
        # Notify staff about a canceled order
        with container:
            st.error(f"🚫 Order {order_id} has been canceled")

    def limited_inventory_notification(self, container):
        # Notify staff of limited inventory
        with container:
            st.warning(f"⚠️ Inventory is running low!")
