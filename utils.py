import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from typing import List, Dict, Any, Optional, Tuple
import re
import base64
from io import BytesIO
from PIL import Image

def format_number(number):
    """
    Format a number with commas as thousands separators.

    Args:
        number (float or int): The number to format

    Returns:
        str: The formatted number as a string
    """
    return f"{number:,.2f}"

def search_amazon_products(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search for products on Amazon based on the query.

    Args:
        query (str): The search query
        max_results (int): Maximum number of results to return

    Returns:
        List[Dict[str, Any]]: List of product dictionaries with name, price, image_url, and url
    """
    # In a real implementation, this would use Amazon's API or web scraping
    # For demo purposes, we'll simulate results
    if not query:
        return []

    # Simulate a search delay
    # In a real implementation, this would be an actual API call

    # Generate mock results based on the query
    results = []
    for i in range(1, max_results + 1):
        product_name = f"{query.title()} Product {i}"
        price = round(10.0 + (i * 5.99), 2)
        results.append({
            "id": f"prod-{i}",
            "name": product_name,
            "price": price,
            "image_url": f"https://via.placeholder.com/150?text={query.replace(' ', '+')}+{i}",
            "url": f"https://amazon.com/dp/B0{i}X{i}Z{i}",
            "tariff": round(price * 0.1, 2)  # 10% tariff for demo
        })

    return results

def get_product_typeahead(query: str, max_results: int = 5) -> List[str]:
    """
    Get typeahead suggestions for product search.

    Args:
        query (str): The partial search query
        max_results (int): Maximum number of suggestions to return

    Returns:
        List[str]: List of product name suggestions
    """
    # In a real implementation, this would use Amazon's API
    # For demo purposes, we'll simulate results
    if not query:
        return []

    # Common product categories to make suggestions more realistic
    categories = ["Electronics", "Books", "Clothing", "Home", "Kitchen", 
                 "Toys", "Sports", "Beauty", "Health", "Automotive"]

    suggestions = []
    query_lower = query.lower()

    # Generate suggestions based on the query
    for category in categories:
        if category.lower().startswith(query_lower) or query_lower in category.lower():
            suggestions.append(category)

        # Add some specific product suggestions
        suggestions.append(f"{category} {query.title()}")
        suggestions.append(f"{query.title()} {category}")

    # Filter and limit results
    filtered_suggestions = [s for s in suggestions if query_lower in s.lower()]
    return filtered_suggestions[:max_results]

def get_image_as_base64(url: str) -> str:
    """
    Convert an image URL to base64 for embedding in HTML.

    Args:
        url (str): The image URL

    Returns:
        str: Base64 encoded image
    """
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))

        # Resize image to thumbnail size
        img.thumbnail((100, 100))

        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        # Return a placeholder image on error
        return "iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAABmJLR0QA/wD/AP+gvaeTAAABQklEQVR4nO3csU0DMRgF4AdKRsgIbJA2I2QDxAYZISMwAqxAg5SsQNiADZIRUj5dFCD3/eTvq2zLliy/4lmWJEmSJEmSJEmSJEmSJEkrMiTZJrlL8pDkJcnjjH1dJ3lK8pbkPcl+xr4WYZ/kJ8nxzOcQZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlkkEEGGWSQQQYZZJBBBhlk0C/YwCJ+wrMpTwAAAABJRU5ErkJggg=="

def save_to_history(product_data: Dict[str, Any], history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Save a product to search history, avoiding duplicates.

    Args:
        product_data (Dict[str, Any]): Product data to save
        history (List[Dict[str, Any]]): Current history list

    Returns:
        List[Dict[str, Any]]: Updated history list
    """
    # Check if product already exists in history
    for item in history:
        if item.get('id') == product_data.get('id'):
            # Move to top of history (most recent)
            history.remove(item)
            history.insert(0, product_data)
            return history

    # Add new product to history
    history.insert(0, product_data)

    # Limit history size to 20 items
    return history[:20]

def get_history_from_cookie(cookie_value: str) -> List[Dict[str, Any]]:
    """
    Parse history data from cookie.

    Args:
        cookie_value (str): JSON string from cookie

    Returns:
        List[Dict[str, Any]]: List of product dictionaries
    """
    if not cookie_value:
        return []

    try:
        return json.loads(cookie_value)
    except:
        return []

def history_to_cookie(history: List[Dict[str, Any]]) -> str:
    """
    Convert history data to JSON string for cookie storage.

    Args:
        history (List[Dict[str, Any]]): List of product dictionaries

    Returns:
        str: JSON string for cookie
    """
    return json.dumps(history)
