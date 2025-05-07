import streamlit as st
import pandas as pd
import extra_streamlit_components as stx
from utils import (
    format_number, 
    search_amazon_products, 
    get_product_typeahead,
    get_image_as_base64,
    save_to_history,
    get_history_from_cookie,
    history_to_cookie
)

def main():
    st.set_page_config(
        page_title="Amazon Product Search",
        page_icon="🛒",
        layout="wide"
    )

    # Initialize cookie manager
    cookie_manager = stx.CookieManager()

    # Set up page title and description
    st.title("🛒 Amazon Product Search")
    st.markdown("""
    Search for products on Amazon.com and view pricing and tariff information.
    Your search history will be saved for future reference.
    """)

    # Get search history from cookies
    history_cookie = cookie_manager.get(cookie="search_history")
    search_history = get_history_from_cookie(history_cookie)

    # Create two columns for the main layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Product Search")

        # Create a container for the search input and button
        search_container = st.container()

        with search_container:
            # Use a form for the search to prevent auto-refresh
            with st.form(key="search_form"):
                # Create a text input for product search
                search_query = st.text_input(
                    "Enter product name:",
                    key="search_input",
                    placeholder="Type product name here...",
                    help="Enter the name of the product you want to search for on Amazon"
                )

                # Add a checkbox for showing product images
                show_images = st.checkbox("Show product images", value=True)

                # Add a search button
                search_button = st.form_submit_button("Search")

        # Display search results
        if search_button and search_query:
            # Search for products
            products = search_amazon_products(search_query)

            if products:
                st.subheader(f"Search Results for '{search_query}'")

                # Create a DataFrame for the results
                df = pd.DataFrame(products)

                # Format the DataFrame for display
                display_df = df.copy()
                display_df['price'] = display_df['price'].apply(lambda x: f"${format_number(x)}")
                display_df['tariff'] = display_df['tariff'].apply(lambda x: f"${format_number(x)}")

                # Rename columns for display
                display_df = display_df.rename(columns={
                    'name': 'Product Name',
                    'price': 'Price',
                    'tariff': 'Tariff'
                })

                # If showing images, add them to the DataFrame
                if show_images:
                    # Create HTML for images
                    def get_image_html(url):
                        return f'<img src="{url}" width="100" />'

                    # Add image column
                    display_df['Image'] = df['image_url'].apply(get_image_html)

                    # Reorder columns to show image first
                    cols = ['Image', 'Product Name', 'Price', 'Tariff']
                    display_df = display_df[cols]

                # Display the DataFrame
                st.write(display_df.to_html(escape=False), unsafe_allow_html=True)

                # Add selected product to history when clicked
                st.subheader("Select a product to add to history:")
                for i, product in enumerate(products):
                    col_img, col_info = st.columns([1, 3])

                    with col_img:
                        if show_images:
                            st.image(product['image_url'], width=100)

                    with col_info:
                        st.write(f"**{product['name']}**")
                        st.write(f"Price: ${format_number(product['price'])}")
                        st.write(f"Tariff: ${format_number(product['tariff'])}")

                        # Add button to select this product
                        if st.button(f"Add to History", key=f"add_{i}"):
                            # Add to history
                            search_history = save_to_history(product, search_history)

                            # Update cookie
                            cookie_manager.set(
                                cookie="search_history",
                                value=history_to_cookie(search_history),
                                expires_at=None
                            )

                            st.success(f"Added '{product['name']}' to your search history!")
                            st.experimental_rerun()
            else:
                st.info(f"No results found for '{search_query}'")

    # Sidebar for typeahead suggestions
    with st.sidebar:
        st.header("Search Suggestions")
        st.write("Start typing in the search box to see suggestions.")

        # Get the current search input value
        current_input = st.session_state.get("search_input", "")

        # Show typeahead suggestions if there's input
        if current_input:
            suggestions = get_product_typeahead(current_input)

            if suggestions:
                st.subheader("Did you mean:")
                for suggestion in suggestions:
                    if st.button(suggestion, key=f"suggest_{suggestion}"):
                        # Set the search input to this suggestion
                        st.session_state["search_input"] = suggestion
                        st.experimental_rerun()

    # Display search history in the second column
    with col2:
        st.header("Search History")

        if search_history:
            for i, product in enumerate(search_history):
                with st.container():
                    st.markdown("---")

                    # Show product image if available
                    if show_images and 'image_url' in product:
                        st.image(product['image_url'], width=100)

                    # Show product details
                    st.write(f"**{product.get('name', 'Unknown Product')}**")

                    if 'price' in product:
                        st.write(f"Price: ${format_number(product['price'])}")

                    if 'tariff' in product:
                        st.write(f"Tariff: ${format_number(product['tariff'])}")

                    # Add a button to remove from history
                    if st.button("Remove", key=f"remove_{i}"):
                        search_history.pop(i)

                        # Update cookie
                        cookie_manager.set(
                            cookie="search_history",
                            value=history_to_cookie(search_history),
                            expires_at=None
                        )

                        st.experimental_rerun()
        else:
            st.info("Your search history will appear here.")
            st.write("Search for products to build your history.")

if __name__ == "__main__":
    main()
