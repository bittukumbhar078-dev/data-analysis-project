"""Small Open Beauty Facts client used by the Beauty Product Explorer."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


PRODUCT_FIELDS = (
    "code,id,product_name,brands,categories,categories_tags,quantity,"
    "ingredients_text,image_front_url,image_url,generic_name,countries,"
    "countries_tags,product_type"
)


def api_request(url, user_agent, timeout=10):
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8")), None
    except HTTPError as error:
        if error.code == 404:
            return None, "No matching beauty product was found."
        return None, "Open Beauty Facts is temporarily unavailable. Please try again."
    except (URLError, TimeoutError, ValueError):
        return None, "Could not reach Open Beauty Facts. Please check your connection and try again."


def value_or_none(value):
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def normalize_product(raw_product):
    """Return only product values that the UI needs. Missing values stay None."""
    if not raw_product:
        return None
    barcode = value_or_none(raw_product.get("code"))
    external_id = value_or_none(raw_product.get("id")) or barcode
    categories = value_or_none(raw_product.get("categories"))
    countries = value_or_none(raw_product.get("countries"))
    return {
        "external_product_id": external_id,
        "barcode": barcode,
        "product_name": value_or_none(raw_product.get("product_name")) or "Unnamed product",
        "brand": value_or_none(raw_product.get("brands")),
        "category": categories,
        "price": None,
        "rating": None,
        "review_count": None,
        "description": value_or_none(raw_product.get("generic_name")),
        "image_url": value_or_none(raw_product.get("image_front_url")) or value_or_none(raw_product.get("image_url")),
        "ingredients": value_or_none(raw_product.get("ingredients_text")),
        "quantity": value_or_none(raw_product.get("quantity")),
        "countries": countries,
        "source": "Open Beauty Facts",
    }


def get_beauty_product(barcode, base_url, user_agent, timeout=10):
    clean_barcode = "".join(character for character in str(barcode) if character.isdigit())
    if not clean_barcode:
        return None, "Enter a valid numeric barcode."
    params = urlencode({"product_type": "beauty", "fields": PRODUCT_FIELDS})
    url = f"{base_url}/api/v3/product/{quote(clean_barcode)}?{params}"
    payload, error = api_request(url, user_agent, timeout)
    if error:
        return None, error
    product = normalize_product(payload.get("product"))
    if not product:
        return None, "No matching beauty product was found."
    return product, None


def search_beauty_products(keyword, brand, category, base_url, user_agent, page=1, page_size=12, timeout=10):
    """Use documented structured search first, then legacy keyword search when needed."""
    params = {"page": page, "page_size": page_size, "fields": PRODUCT_FIELDS}
    if brand or category:
        if brand:
            params["brands_tags_en"] = brand.strip().lower()
        if category:
            params["categories_tags_en"] = category.strip().lower()
        url = f"{base_url}/api/v2/search?{urlencode(params)}"
    elif keyword:
        params.update({"search_terms": keyword.strip(), "json": 1})
        url = f"{base_url}/cgi/search.pl?{urlencode(params)}"
    else:
        return [], None

    payload, error = api_request(url, user_agent, timeout)
    if error:
        return [], error
    products = [normalize_product(product) for product in payload.get("products", [])]
    return [product for product in products if product], None


def save_product_to_database(cursor, product):
    """Insert or refresh an API product. Barcode prevents repeated cached records."""
    barcode = product.get("barcode")
    if not barcode:
        return None
    columns = (
        product.get("external_product_id"), barcode, product.get("product_name"), product.get("brand"),
        product.get("category"), product.get("price"), product.get("rating"), product.get("review_count"),
        product.get("description"), product.get("image_url"), product.get("ingredients"), product.get("quantity"),
        product.get("countries"), product.get("source", "Open Beauty Facts"),
    )
    cursor.execute(
        """INSERT INTO beauty_products
        (external_product_id, barcode, product_name, brand, category, price, rating, review_count,
         description, image_url, ingredients, quantity, countries, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            external_product_id = VALUES(external_product_id), product_name = VALUES(product_name),
            brand = VALUES(brand), category = VALUES(category), price = VALUES(price),
            rating = VALUES(rating), review_count = VALUES(review_count), description = VALUES(description),
            image_url = VALUES(image_url), ingredients = VALUES(ingredients), quantity = VALUES(quantity),
            countries = VALUES(countries), source = VALUES(source)""",
        columns,
    )
    cursor.execute("SELECT id FROM beauty_products WHERE barcode = %s", (barcode,))
    row = cursor.fetchone()
    return row[0] if row else None
