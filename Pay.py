import stripe
import streamlit as st
from decimal import Decimal, ROUND_DOWN

# Initialize Stripe with your secret key
stripe.api_key = "sk_test_51Q91IjBqPaIchBVHOjUCH6Y9sqllMTW16SEHe7Jct82TEFHRPWGmuAkE5lsoQgxB4JHL5WC3cdwicHSQLFh0zUgu00wa9qx8eV"

def calculate_discounted_prices(selected_items_with_quantities, promo_discount_percentage, points_discount_value):
    discounted_prices = []
    total_discounted_price = Decimal(0)
    # Calculate total quantity for point discount calculation
    total_quantity = sum(quantity for _, _, quantity in selected_items_with_quantities)

    # Track remaining points discount
    remaining_points_discount = points_discount_value

    for idx, (item, price, quantity) in enumerate(selected_items_with_quantities):
        # Calculate the total price for the item before discounts
        total_price = Decimal(price)

        # Calculate the promo discount
        promo_discount_amount = (promo_discount_percentage / Decimal(100)) * total_price
        promo_discount_amount = promo_discount_amount.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

        # Calculate points discount for this item
        if idx < len(selected_items_with_quantities) - 1:  # For all items except the last
            points_discount_amount = (points_discount_value / Decimal(total_quantity) * quantity).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            remaining_points_discount -= points_discount_amount
        else:  # For the last item, assign the remaining discount
            points_discount_amount = remaining_points_discount.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

        # Calculate the final discounted price
        discounted_price = total_price - promo_discount_amount - points_discount_amount
        discounted_price = discounted_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        discounted_price = max(discounted_price, Decimal(0))  # Ensure price is not negative

        # Append to the list and accumulate total
        discounted_prices.append(discounted_price)
        total_discounted_price += discounted_price

    # Ensure total_discounted_price is rounded consistently
    total_discounted_price = total_discounted_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    return discounted_prices, total_discounted_price

def create_checkout_session(selected_items_with_quantities, promo_discount_percentage, points_discount_value):
    line_items = []

    # Get discounted prices and total discounted price
    discounted_prices, total_discounted_price = calculate_discounted_prices(
        selected_items_with_quantities,
        promo_discount_percentage,
        points_discount_value
    )

    # Ensure total_discounted_price is rounded consistently
    total_discounted_price = total_discounted_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    # Create the line items for Stripe checkout session based on selected items and quantities
    for (item, price, quantity), discounted_price in zip(selected_items_with_quantities, discounted_prices):
        # Create a line item with original and discounted prices in the description
        line_items.append({
            'price_data': {
                'currency': 'myr',
                'product_data': {
                    'name': item,
                    'description': f"Original Unit Price: MYR {Decimal(price)/quantity:.2f}, Quantity: {quantity}",
                },
                'unit_amount': int(discounted_price * 100),  # Stripe expects amount in cents per unit
            },
            'quantity': 1,
        })

    # Try to create the session and handle any possible errors
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card', 'grabpay', 'fpx'],
            line_items=line_items,
            mode='payment',
            success_url=f'https://twilightcoffeeshop.streamlit.app/?payment=success',  # Success payment URL
            cancel_url=f'https://twilightcoffeeshop.streamlit.app/?payment=fail',      # Fail payment URL
        )
        return session
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None