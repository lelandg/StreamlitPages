# ─────────────────────────────────────────────────────────────────────────────
# CSS Style Sheet Creator
# ─────────────────────────────────────────────────────────────────────────────
# This script allows users to enter a URL, extract CSS styles from the page,
# and interactively edit and customize those styles. Users can preview each style,
# copy individual styles or the combined CSS, download the entire CSS file,
# and share their creations with others.
import traceback

import streamlit as st
import requests
import json
import os
import uuid
import base64
import io
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import cssutils
import extra_streamlit_components as stx

# Suppress cssutils warnings
import logging
cssutils.log.setLevel(logging.CRITICAL)

# Set page config - must be the first Streamlit command
st.set_page_config(
    page_title="CSS Style Sheet Creator",
    layout="wide",
    page_icon="favicon.png"
)

# ── Imports ────────────────────────────────────────────────────────────────────
import streamlit as st
import extra_streamlit_components as stx         # ← already required elsewhere
# … any other imports …

# ── Globals ────────────────────────────────────────────────────────────────────
_COOKIE_MANAGER: stx.CookieManager | None = None          #  NEW
_COOKIE_MANAGER_KEY = "cookie_manager"                    #  NEW

# ─────────────────────────────────────────────────────────────────────────────
# Directory and file management
# ─────────────────────────────────────────────────────────────────────────────

def ensure_directories_exist():
    """Create necessary directories if they don't exist"""
    os.makedirs("data/css_styles", exist_ok=True)
    os.makedirs("data/shared_styles", exist_ok=True)
    os.makedirs("data/users", exist_ok=True)

# Ensure directories exist
ensure_directories_exist()

# ─────────────────────────────────────────────────────────────────────────────
# Cookie management
# ─────────────────────────────────────────────────────────────────────────────

def get_cookie_manager() -> "stx.CookieManager":
    """
    Lazily create (or return) a single, reusable CookieManager instance.

    Avoids StreamlitDuplicateElementKey by ensuring the component
    is rendered with the same key only once per app session.
    """
    global _COOKIE_MANAGER

    # If we've already created the component, just return it.
    if _COOKIE_MANAGER is not None:
        return _COOKIE_MANAGER

    # Otherwise create it exactly once, with an explicit unique key.
    _COOKIE_MANAGER = stx.CookieManager(key=_COOKIE_MANAGER_KEY)
    return _COOKIE_MANAGER

def get_user_id():
    """Get a unique user ID from cookie or create one if it doesn't exist"""
    cookie_manager = get_cookie_manager()
    user_id = cookie_manager.get("user_id")

    if not user_id:
        user_id = str(uuid.uuid4())
        cookie_manager.set("user_id", user_id, expires_at=datetime(year=2030, month=1, day=1))

    return user_id

def get_url_history():
    """Get URL history from cookie"""
    cookie_manager = get_cookie_manager()
    history_json = cookie_manager.get("url_history")

    if history_json:
        try:
            return json.loads(history_json)
        except json.JSONDecodeError:
            return []
    return []

def save_url_to_history(url):
    """Save URL to history cookie"""
    cookie_manager = get_cookie_manager()
    history = get_url_history()

    # Check if URL already exists in history
    for entry in history:
        if isinstance(entry, dict) and entry.get("url") == url:
            # Update timestamp
            entry["timestamp"] = datetime.now().isoformat()
            cookie_manager.set("url_history", json.dumps(history), expires_at=datetime(year=2030, month=1, day=1))
            return

    # Add new entry
    history.append({
        "url": url,
        "timestamp": datetime.now().isoformat()
    })

    # Limit history to 20 entries
    if len(history) > 20:
        history = history[-20:]

    cookie_manager.set("url_history", json.dumps(history), expires_at=datetime(year=2030, month=1, day=1))

# ─────────────────────────────────────────────────────────────────────────────
# CSS extraction and parsing
# ─────────────────────────────────────────────────────────────────────────────

def fetch_webpage(url):
    """Fetch a webpage and return its content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        st.error(f"Error fetching webpage: {e}")
        st.error(f"{traceback.format_exc().replace("\n", "<br>")}", unsafe_allow_html=True)
        return None

def extract_css_from_html(html_content, base_url):
    """Extract CSS from HTML content"""
    if not html_content:
        return {}

    soup = BeautifulSoup(html_content, 'html.parser')
    css_rules = {}
    styles_css_found = False

    # Extract inline styles from <style> tags
    for style_tag in soup.find_all('style'):
        if style_tag.string:
            try:
                sheet = cssutils.parseString(style_tag.string)
                for rule in sheet:
                    if rule.type == rule.STYLE_RULE:
                        selector = rule.selectorText
                        if selector not in css_rules:
                            css_rules[selector] = {}

                        for property in rule.style:
                            css_rules[selector][property.name] = property.value
            except:
                pass

    # Extract linked stylesheets
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            # Check if this is styles.css
            if 'styles.css' in href:
                styles_css_found = True

            # Handle relative URLs
            if href.startswith('/'):
                if base_url.endswith('/'):
                    href = base_url + href[1:]
                else:
                    href = base_url + href
            elif not href.startswith(('http://', 'https://')):
                if base_url.endswith('/'):
                    href = base_url + href
                else:
                    href = base_url + '/' + href

            try:
                css_content = fetch_webpage(href)
                if css_content:
                    sheet = cssutils.parseString(css_content)
                    for rule in sheet:
                        if rule.type == rule.STYLE_RULE:
                            selector = rule.selectorText
                            if selector not in css_rules:
                                css_rules[selector] = {}

                            for property in rule.style:
                                css_rules[selector][property.name] = property.value
            except:
                pass

    # If styles.css is not found, extract inline styles from HTML elements
    if not styles_css_found:
        # Find all elements with style attributes
        elements_with_style = soup.find_all(lambda tag: tag.has_attr('style'))

        # Process each element with inline style
        for element in elements_with_style:
            # Create a unique selector for this element
            # Use tag name, id, and classes to make it specific
            tag_name = element.name
            element_id = element.get('id', '')
            classes = element.get('class', [])

            # Build the selector
            selector_parts = [tag_name]
            if element_id:
                selector_parts.append(f"#{element_id}")
            if classes:
                selector_parts.extend([f".{cls}" for cls in classes])

            # Join the parts to create a selector
            selector = ''.join(selector_parts) if len(selector_parts) == 1 else ' '.join(selector_parts)

            # If we couldn't create a specific selector, use a more generic one with a unique attribute
            if selector == tag_name:
                # Add a unique attribute if possible
                for attr in ['name', 'href', 'src', 'alt', 'title']:
                    if element.has_attr(attr):
                        attr_value = element[attr]
                        # Escape special characters in attribute value
                        attr_value = attr_value.replace('"', '\\"')
                        selector = f"{tag_name}[{attr}=\"{attr_value}\"]"
                        break

            # If we still don't have a specific selector, use a positional one
            if selector == tag_name:
                # Find the position of this element among siblings of the same type
                siblings = element.find_parent().find_all(tag_name, recursive=False)
                position = siblings.index(element) + 1
                selector = f"{tag_name}:nth-of-type({position})"

            # Parse the inline style
            style_text = element['style']
            try:
                # Create a temporary style rule to parse the inline style
                temp_css = f"temp {{ {style_text} }}"
                sheet = cssutils.parseString(temp_css)

                # Extract properties
                if selector not in css_rules:
                    css_rules[selector] = {}

                for rule in sheet:
                    if rule.type == rule.STYLE_RULE:
                        for property in rule.style:
                            css_rules[selector][property.name] = property.value
            except:
                pass

    return css_rules

def categorize_css_rules(css_rules):
    """Categorize CSS rules into groups for better organization"""
    categories = {
        "Typography": [],
        "Layout": [],
        "Colors": [],
        "Borders": [],
        "Backgrounds": [],
        "Tables": [],
        "Forms": [],
        "Animations": [],
        "Other": []
    }

    typography_props = ['font', 'font-family', 'font-size', 'font-weight', 'line-height', 'text-align', 'text-decoration', 'text-transform']
    layout_props = ['display', 'position', 'width', 'height', 'margin', 'padding', 'flex', 'grid', 'float']
    color_props = ['color', 'opacity']
    border_props = ['border', 'border-radius', 'box-shadow', 'outline']
    background_props = ['background', 'background-color', 'background-image']
    table_props = ['table', 'tr', 'td', 'th', 'tbody', 'thead']
    form_props = ['input', 'button', 'select', 'textarea', 'form']
    animation_props = ['animation', 'transition', 'transform']

    for selector, properties in css_rules.items():
        # Check if selector contains specific keywords for categories
        if any(keyword in selector.lower() for keyword in table_props):
            categories["Tables"].append((selector, properties))
            continue
        elif any(keyword in selector.lower() for keyword in form_props):
            categories["Forms"].append((selector, properties))
            continue

        # Check properties to determine category
        has_typography = any(prop in properties for prop in typography_props)
        has_layout = any(prop in properties for prop in layout_props)
        has_color = any(prop in properties for prop in color_props)
        has_border = any(prop in properties for prop in border_props)
        has_background = any(prop in properties for prop in background_props)
        has_animation = any(prop in properties for prop in animation_props)

        # Determine primary category based on property count
        counts = {
            "Typography": sum(1 for prop in properties if prop in typography_props),
            "Layout": sum(1 for prop in properties if prop in layout_props),
            "Colors": sum(1 for prop in properties if prop in color_props),
            "Borders": sum(1 for prop in properties if prop in border_props),
            "Backgrounds": sum(1 for prop in properties if prop in background_props),
            "Animations": sum(1 for prop in properties if prop in animation_props)
        }

        if max(counts.values(), default=0) > 0:
            primary_category = max(counts.items(), key=lambda x: x[1])[0]
            categories[primary_category].append((selector, properties))
        else:
            categories["Other"].append((selector, properties))

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}

# ─────────────────────────────────────────────────────────────────────────────
# Style preview and editing
# ─────────────────────────────────────────────────────────────────────────────

def generate_preview_html(selector, properties):
    """Generate HTML preview for a CSS rule"""
    # Create a style string from properties
    style_str = '; '.join([f"{prop}: {value}" for prop, value in properties.items()])

    # Determine what kind of preview to show based on the selector
    preview_content = ""

    if any(keyword in selector.lower() for keyword in ['table', 'tr', 'td', 'th']):
        # Table preview
        preview_content = f"""
        <table style="{style_str}">
            <tr>
                <th>Header 1</th>
                <th>Header 2</th>
            </tr>
            <tr>
                <td>Row 1, Cell 1</td>
                <td>Row 1, Cell 2</td>
            </tr>
            <tr>
                <td>Row 2, Cell 1</td>
                <td>Row 2, Cell 2</td>
            </tr>
        </table>
        """
    elif any(keyword in selector.lower() for keyword in ['button']):
        # Button preview
        preview_content = f'<button style="{style_str}">Button</button>'
    elif any(keyword in selector.lower() for keyword in ['input', 'form']):
        # Form input preview
        preview_content = f'<input type="text" style="{style_str}" value="Input Text">'
    elif any(keyword in selector.lower() for keyword in ['a', 'link']):
        # Link preview
        preview_content = f'<a href="#" style="{style_str}">Link Text</a>'
    elif any(keyword in selector.lower() for keyword in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        # Heading preview
        heading_level = next((h for h in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] if h in selector.lower()), 'h2')
        preview_content = f'<{heading_level} style="{style_str}">Heading</{heading_level}>'
    elif any(keyword in selector.lower() for keyword in ['p', 'text']):
        # Paragraph preview
        preview_content = f'<p style="{style_str}">This is a paragraph of text that demonstrates the styling.</p>'
    elif 'body' in selector.lower() or 'html' in selector.lower():
        # Body/container preview
        preview_content = f'<div style="{style_str}; padding: 10px;">Container with body styles</div>'
    else:
        # Generic div preview
        preview_content = f'<div style="{style_str}; padding: 10px;">Generic element with styles</div>'

    return f"""
    <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 10px;">
        <p><strong>Selector:</strong> {selector}</p>
        <div style="margin-top: 10px;">
            {preview_content}
        </div>
    </div>
    """

def get_css_string(selector, properties):
    """Convert a CSS rule to a string"""
    props_str = '\n    '.join([f"{prop}: {value};" for prop, value in properties.items()])
    return f"{selector} {{\n    {props_str}\n}}"

def get_combined_css(css_rules):
    """Combine all CSS rules into a single string"""
    css_strings = []
    for selector, properties in css_rules.items():
        css_strings.append(get_css_string(selector, properties))
    return '\n\n'.join(css_strings)

# ─────────────────────────────────────────────────────────────────────────────
# Sharing and storage
# ─────────────────────────────────────────────────────────────────────────────

def save_shared_style(css_rules, user_info=None):
    """Save a shared style to the server"""
    # Generate a unique ID for the shared style
    style_id = str(uuid.uuid4())

    # Create the data to save
    shared_data = {
        "id": style_id,
        "css_rules": css_rules,
        "created_at": datetime.now().isoformat(),
        "user_info": user_info or {}
    }

    # Save to file
    file_path = f"data/shared_styles/{style_id}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(shared_data, f, indent=2)

    return style_id

def get_shared_style(style_id):
    """Get a shared style by ID"""
    file_path = f"data/shared_styles/{style_id}.json"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_all_shared_styles():
    """Get all shared styles"""
    shared_styles = []
    shared_dir = "data/shared_styles"

    if os.path.exists(shared_dir):
        for filename in os.listdir(shared_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(shared_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        style_data = json.load(f)
                        shared_styles.append(style_data)
                except:
                    pass

    # Sort by creation date (newest first)
    shared_styles.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return shared_styles

# ─────────────────────────────────────────────────────────────────────────────
# UI Components
# ─────────────────────────────────────────────────────────────────────────────

def display_url_input():
    """Display URL input and history"""
    st.subheader("Enter a URL to extract CSS styles")

    # URL input
    url = st.text_input("Website URL", placeholder="https://example.com")

    # URL history
    history = get_url_history()
    if history:
        st.subheader("URL History")

        # Create a grid layout for history
        cols = st.columns(3)
        for i, entry in enumerate(history):
            if isinstance(entry, dict) and 'url' in entry:
                col_idx = i % 3
                with cols[col_idx]:
                    if st.button(f"{entry['url']}", key=f"history_{i}"):
                        return entry['url']

    return url if url else None

def display_user_info_form():
    """Display user info form for sharing"""
    with st.form("user_info_form"):
        st.subheader("Your Information (Optional)")
        name = st.text_input("Name")
        email = st.text_input("Email")
        website = st.text_input("Website")

        submit = st.form_submit_button("Save Information")

        if submit:
            return {
                "name": name,
                "email": email,
                "website": website
            }
    return None

def display_style_editor(css_rules):
    """Display the interactive style editor"""
    if not css_rules:
        st.warning("No CSS styles found. Try another URL.")
        return css_rules

    st.subheader("CSS Style Editor")

    # Option to edit values with textboxes
    edit_values = st.checkbox("Edit values with textboxes", value=False)

    # Categorize CSS rules
    categorized_rules = categorize_css_rules(css_rules)

    # Create tabs for categories
    tabs = st.tabs(list(categorized_rules.keys()))

    # Updated rules dictionary
    updated_rules = css_rules.copy()

    # Display rules by category
    for i, (category, rules) in enumerate(categorized_rules.items()):
        with tabs[i]:
            for selector, properties in rules:
                with st.expander(f"{selector}", expanded=False):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.markdown("### Preview")
                        st.markdown(generate_preview_html(selector, properties), unsafe_allow_html=True)

                    with col2:
                        st.markdown("### CSS")
                        css_text = get_css_string(selector, properties)
                        st.code(css_text, language="css")

                        # Copy button for this style
                        if st.button("Copy CSS", key=f"copy_{selector}"):
                            st.code(css_text, language="css")
                            st.success("CSS copied to clipboard!")

                    # Property editor
                    st.markdown("### Edit Properties")

                    # Create a copy of properties to modify
                    updated_properties = properties.copy()

                    # Display property editors
                    for prop, value in properties.items():
                        if edit_values:
                            # Text input for editing
                            new_value = st.text_input(f"{prop}", value=value, key=f"{selector}_{prop}")
                        else:
                            # Interactive widgets based on property type
                            if prop in ['color', 'background-color', 'border-color']:
                                new_value = st.color_picker(f"{prop}", value=value, key=f"{selector}_{prop}")
                            elif prop in ['width', 'height', 'margin', 'padding'] and any(unit in value for unit in ['px', 'em', 'rem', '%']):
                                # Extract numeric value and unit
                                import re
                                match = re.match(r'(\d+)([a-z%]+)', value)
                                if match:
                                    num_val, unit = match.groups()
                                    new_num_val = st.slider(f"{prop} ({unit})", 0, 100, int(num_val), key=f"{selector}_{prop}")
                                    new_value = f"{new_num_val}{unit}"
                                else:
                                    new_value = st.text_input(f"{prop}", value=value, key=f"{selector}_{prop}")
                            elif prop == 'font-weight':
                                options = ['normal', 'bold', '100', '200', '300', '400', '500', '600', '700', '800', '900']
                                new_value = st.selectbox(f"{prop}", options, index=options.index(value) if value in options else 0, key=f"{selector}_{prop}")
                            elif prop == 'text-align':
                                options = ['left', 'center', 'right', 'justify']
                                new_value = st.selectbox(f"{prop}", options, index=options.index(value) if value in options else 0, key=f"{selector}_{prop}")
                            elif prop == 'display':
                                options = ['block', 'inline', 'inline-block', 'flex', 'grid', 'none']
                                new_value = st.selectbox(f"{prop}", options, index=options.index(value) if value in options else 0, key=f"{selector}_{prop}")
                            else:
                                new_value = st.text_input(f"{prop}", value=value, key=f"{selector}_{prop}")

                        # Update the property if changed
                        if new_value != value:
                            updated_properties[prop] = new_value

                    # Update the rules dictionary with modified properties
                    updated_rules[selector] = updated_properties

    return updated_rules

def display_combined_css(css_rules):
    """Display the combined CSS with download and copy options"""
    if not css_rules:
        return

    st.markdown("---")
    st.subheader("Combined CSS")

    combined_css = get_combined_css(css_rules)

    # Display the combined CSS
    st.code(combined_css, language="css")

    col1, col2 = st.columns(2)

    with col1:
        # Copy button
        if st.button("Copy All CSS"):
            st.code(combined_css, language="css")
            st.success("All CSS copied to clipboard!")

    with col2:
        # Download button
        if st.button("Download CSS"):
            # Create a download link
            b64 = base64.b64encode(combined_css.encode()).decode()
            href = f'<a href="data:text/css;base64,{b64}" download="styles.css">Download CSS File</a>'
            st.markdown(href, unsafe_allow_html=True)

def display_sharing_options(css_rules):
    """Display options for sharing styles"""
    if not css_rules:
        return

    st.markdown("---")
    st.subheader("Share Your CSS")

    # User info collection
    with st.expander("Add Your Information (Optional)"):
        user_info = display_user_info_form()

    # Save and share button
    if st.button("Save & Share"):
        style_id = save_shared_style(css_rules, user_info)
        share_url = f"{st.query_params.get('server_url', [''])[0]}/streamlit_styles?style_id={style_id}"
        st.success("Your CSS has been saved and can be shared!")
        st.code(share_url)
        st.markdown(f"[Open Shared Link]({share_url})")

def display_shared_styles_browser():
    """Display a browser for shared styles"""
    st.markdown("---")
    st.subheader("Browse Shared Styles")

    shared_styles = get_all_shared_styles()

    if not shared_styles:
        st.info("No shared styles found.")
        return

    # Create a grid layout for shared styles
    for i in range(0, len(shared_styles), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(shared_styles):
                style = shared_styles[i + j]
                with cols[j]:
                    st.markdown(f"**Created:** {style.get('created_at', 'Unknown')[:10]}")
                    if style.get('user_info', {}).get('name'):
                        st.markdown(f"**By:** {style['user_info']['name']}")

                    # Preview button
                    if st.button("View Style", key=f"view_{style['id']}"):
                        return style['id']

    return None

# ─────────────────────────────────────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────────────────────────────────────

def main():
    st.title("CSS Style Sheet Creator")
    st.markdown("Extract, edit, and share CSS styles from any website.")

    # Initialize session state for storing CSS rules
    if "css_rules" not in st.session_state:
        st.session_state.css_rules = {}

    # Check for shared style in URL
    query_params = st.query_params
    if "style_id" in query_params:
        style_id = query_params["style_id"][0]
        shared_style = get_shared_style(style_id)

        if shared_style:
            st.success("Viewing a shared style sheet!")
            st.session_state.css_rules = shared_style["css_rules"]

            # Display user info if available
            if shared_style.get("user_info", {}).get("name"):
                st.markdown(f"**Created by:** {shared_style['user_info']['name']}")

            # Display creation date
            if shared_style.get("created_at"):
                st.markdown(f"**Created on:** {shared_style['created_at'][:10]}")

    # URL input and history
    url = display_url_input()

    # Process URL if provided
    if url and st.button("Extract CSS"):
        with st.spinner("Fetching and parsing CSS..."):
            html_content = fetch_webpage(url)
            if html_content:
                css_rules = extract_css_from_html(html_content, url)
                if css_rules:
                    st.session_state.css_rules = css_rules
                    save_url_to_history(url)
                    st.success(f"Found {len(css_rules)} CSS rules!")
                else:
                    st.warning("No CSS rules found on this page.")

    # Display style editor if we have CSS rules
    if st.session_state.css_rules:
        updated_rules = display_style_editor(st.session_state.css_rules)

        # Update session state with edited rules
        if updated_rules != st.session_state.css_rules:
            st.session_state.css_rules = updated_rules

        # Display combined CSS with download and copy options
        display_combined_css(st.session_state.css_rules)

        # Display sharing options
        display_sharing_options(st.session_state.css_rules)

    # Browse shared styles
    selected_style_id = display_shared_styles_browser()
    if selected_style_id:
        # Update URL to view the selected style
        st.experimental_set_query_params(style_id=selected_style_id)
        st.experimental_rerun()

if __name__ == "__main__":
    main()