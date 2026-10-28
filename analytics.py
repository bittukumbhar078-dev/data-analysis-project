"""Generic and beauty-specific analysis helpers for DataLens Beauty."""
import math
import re
import numpy as np
import pandas as pd

BEAUTY_COLUMNS = {
    "product_name": ["product_name", "product name", "product", "name"],
    "brand": ["brand", "brand_name", "brand name"],
    "category": ["category", "product_category", "product category"],
    "price": ["price", "selling_price", "selling price", "price_inr", "mrp"],
    "rating": ["rating", "review_rating", "rating_score", "rating score"],
    "review_count": ["review_count", "reviews", "review count", "number_of_reviews"],
}


def read_dataset(path, extension):
    data = pd.read_csv(path) if extension == "csv" else pd.read_excel(path)
    data.columns = [str(column).strip() for column in data.columns]
    data = data.loc[:, ~data.columns.duplicated()]
    if data.empty or len(data.columns) == 0:
        raise ValueError("The file has no usable rows or columns.")
    return data


def _date_values(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")
    if pd.api.types.is_numeric_dtype(series):
        return pd.Series(pd.NaT, index=series.index)
    values = series.dropna().astype(str).head(250)
    if values.empty:
        return pd.Series(pd.NaT, index=series.index)
    parsed = pd.to_datetime(values, errors="coerce", format="mixed")
    if parsed.notna().mean() >= 0.8:
        return pd.to_datetime(series, errors="coerce", format="mixed")
    return pd.Series(pd.NaT, index=series.index)


def detect_column_types(data):
    detected = {}
    for name in data.columns:
        series = data[name]
        non_empty = series.dropna()
        unique = non_empty.nunique()
        total = max(len(non_empty), 1)
        lower_name = str(name).lower()
        if non_empty.empty:
            kind = "Text"
        elif pd.api.types.is_bool_dtype(series) or set(non_empty.astype(str).str.lower().unique()).issubset({"true", "false", "yes", "no", "0", "1"}):
            kind = "Boolean"
        elif "id" in lower_name and unique / total > 0.75:
            kind = "ID"
        elif pd.api.types.is_numeric_dtype(series):
            kind = "ID" if unique / total > 0.95 and unique > 10 else "Numeric"
        elif _date_values(series).notna().mean() >= 0.8:
            kind = "Date"
        elif unique <= min(20, max(5, total * 0.25)):
            kind = "Categorical"
        else:
            kind = "Text"
        detected[name] = kind
    return detected


def profile_dataset(data):
    types = detect_column_types(data)
    columns = [{"name": str(name), "type": types[name], "dtype": str(data[name].dtype),
                "missing": int(data[name].isna().sum()), "unique": int(data[name].nunique())}
               for name in data.columns]
    return {"rows": int(len(data)), "columns": int(len(data.columns)), "missing": int(data.isna().sum().sum()),
            "duplicates": int(data.duplicated().sum()), "column_profiles": columns, "types": types}


def clean_dataset(data):
    original = profile_dataset(data)
    work = data.copy()
    actions = []
    before_rows = len(work)
    work = work.dropna(axis=0, how="all")
    empty_rows = before_rows - len(work)
    if empty_rows:
        actions.append(f"Removed {empty_rows} completely empty row(s).")
    before_columns = len(work.columns)
    work = work.dropna(axis=1, how="all")
    if before_columns - len(work.columns):
        actions.append(f"Removed {before_columns - len(work.columns)} completely empty column(s).")
    duplicate_count = int(work.duplicated().sum())
    work = work.drop_duplicates()
    if duplicate_count:
        actions.append(f"Removed {duplicate_count} duplicate row(s).")
    invalid = 0
    for name in work.select_dtypes(include="object").columns:
        work[name] = work[name].map(lambda value: value.strip() if isinstance(value, str) else value)
    if len(work.select_dtypes(include="object").columns):
        actions.append("Trimmed extra spaces from text values.")
    types = detect_column_types(work)
    for name, kind in types.items():
        if kind == "Date":
            old_count = work[name].notna().sum()
            work[name] = _date_values(work[name])
            invalid += max(0, old_count - work[name].notna().sum())
        elif kind == "Numeric":
            numeric = pd.to_numeric(work[name], errors="coerce")
            invalid += max(0, work[name].notna().sum() - numeric.notna().sum())
            work[name] = numeric
    types = detect_column_types(work)
    for name, kind in types.items():
        if work[name].isna().sum() == 0:
            continue
        if kind == "Numeric" and work[name].notna().any():
            work[name] = work[name].fillna(work[name].median())
            actions.append(f"Filled missing numeric values in {name} with the median.")
        elif kind in ("Categorical", "Boolean") and work[name].notna().any():
            mode = work[name].mode()
            if not mode.empty:
                work[name] = work[name].fillna(mode.iloc[0])
                actions.append(f"Filled missing category values in {name} with the most frequent value.")
        elif kind == "Text":
            work[name] = work[name].fillna("Unknown")
            actions.append(f"Marked missing text values in {name} as Unknown.")
    if invalid:
        actions.append(f"Found {invalid} value(s) that could not be converted safely.")
    return work, {"before": original, "after": profile_dataset(work), "actions": actions or ["No cleaning changes were needed."],
                  "invalid": invalid, "empty_rows": empty_rows, "duplicates_removed": duplicate_count}


def _safe_number(value):
    value = float(value)
    return round(value, 2) if math.isfinite(value) else 0


def _normalized_name(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def detect_beauty_columns(data):
    normalized = {_normalized_name(name): name for name in data.columns}
    matches = {}
    for field, aliases in BEAUTY_COLUMNS.items():
        for alias in aliases:
            found = normalized.get(_normalized_name(alias))
            if found:
                matches[field] = found
                break
    return matches


def _numeric_series(data, column):
    return pd.to_numeric(data[column], errors="coerce").dropna()


def _chart(title, chart_type, labels=None, values=None, points=None, horizontal=False):
    chart = {"title": title, "type": chart_type}
    if labels is not None:
        chart["labels"] = [str(value) for value in labels]
    if values is not None:
        chart["values"] = [_safe_number(value) for value in values]
    if points is not None:
        chart["points"] = points
    if horizontal:
        chart["horizontal"] = True
    return chart


def generate_beauty_dashboard(data, beauty_columns):
    profile = profile_dataset(data)
    kpis = [{"label": "Total Products", "value": f"{len(data):,}", "note": "Records in uploaded dataset", "icon": "bi-box-seam"}]
    category, brand = beauty_columns.get("category"), beauty_columns.get("brand")
    product_name, price = beauty_columns.get("product_name"), beauty_columns.get("price")
    rating, reviews = beauty_columns.get("rating"), beauty_columns.get("review_count")

    if price and not _numeric_series(data, price).empty:
        kpis.append({"label": "Average Price", "value": f"₹{_safe_number(_numeric_series(data, price).mean()):,}", "note": "Available price values", "icon": "bi-currency-rupee"})
    if rating and not _numeric_series(data, rating).empty:
        kpis.append({"label": "Average Rating", "value": f"{_safe_number(_numeric_series(data, rating).mean())} / 5", "note": "Available rating values", "icon": "bi-star"})
    if reviews and not _numeric_series(data, reviews).empty:
        kpis.append({"label": "Total Reviews", "value": f"{int(_numeric_series(data, reviews).sum()):,}", "note": "Reported review volume", "icon": "bi-chat-square-text"})
    if category:
        kpis.append({"label": "Categories", "value": str(data[category].nunique()), "note": "Unique category values", "icon": "bi-grid-3x3-gap"})
    if brand and len(kpis) < 6:
        kpis.append({"label": "Brands", "value": str(data[brand].nunique()), "note": "Unique brand values", "icon": "bi-tags"})

    charts, insights = [], []
    if category:
        counts = data[category].fillna("Not available").value_counts().head(10)
        charts.append(_chart("Products by Category", "bar", counts.index, counts.values))
        if not counts.empty:
            insights.append(f"{counts.index[0]} represents the largest category in this uploaded dataset ({int(counts.iloc[0]):,} products).")
    if brand:
        counts = data[brand].fillna("Not available").value_counts().head(10)
        charts.append(_chart("Products by Brand", "bar", counts.index, counts.values, horizontal=True))
    if rating and not _numeric_series(data, rating).empty:
        values = _numeric_series(data, rating)
        hist, edges = np.histogram(values, bins=min(8, max(3, values.nunique())))
        labels = [f"{edges[index]:.1f}–{edges[index + 1]:.1f}" for index in range(len(hist))]
        charts.append(_chart("Rating Distribution", "bar", labels, hist))
    if price and rating:
        values = data[[price, rating]].copy()
        values[price] = pd.to_numeric(values[price], errors="coerce")
        values[rating] = pd.to_numeric(values[rating], errors="coerce")
        values = values.dropna().head(300)
        if not values.empty:
            charts.append(_chart("Price vs Rating", "scatter", points=[{"x": _safe_number(row[0]), "y": _safe_number(row[1])} for row in values.values]))
    if reviews and category:
        review_data = data[[category, reviews]].copy()
        review_data[reviews] = pd.to_numeric(review_data[reviews], errors="coerce")
        grouped = review_data.dropna().groupby(category)[reviews].sum().sort_values(ascending=False).head(10)
        if not grouped.empty:
            charts.append(_chart("Review Count by Category", "bar", grouped.index, grouped.values))
    if reviews and product_name and len(charts) < 6:
        review_data = data[[product_name, reviews]].copy()
        review_data[reviews] = pd.to_numeric(review_data[reviews], errors="coerce")
        ranked = review_data.dropna().sort_values(reviews, ascending=False).head(10)
        if not ranked.empty:
            charts.append(_chart("Most Reviewed Products", "bar", ranked[product_name], ranked[reviews], horizontal=True))

    fields = [{"field": field.replace("_", " ").title(), "column": column} for field, column in beauty_columns.items()]
    tables = [{"title": "Available Beauty Dataset Fields", "kind": "beauty_fields", "rows": fields}]
    if price and not _numeric_series(data, price).empty:
        prices = _numeric_series(data, price)
        insights.append(f"Available prices range from ₹{_safe_number(prices.min()):,} to ₹{_safe_number(prices.max()):,}.")
    if rating and brand:
        rating_data = data[[brand, rating]].copy()
        rating_data[rating] = pd.to_numeric(rating_data[rating], errors="coerce")
        grouped = rating_data.dropna().groupby(brand)[rating].agg(["mean", "count"])
        grouped = grouped[grouped["count"] >= 2].sort_values("mean", ascending=False)
        if not grouped.empty:
            insights.append(f"{grouped.index[0]} has the highest average rating among brands with at least two recorded products ({_safe_number(grouped.iloc[0]['mean'])} / 5).")
    if reviews and product_name:
        review_data = data[[product_name, reviews]].copy()
        review_data[reviews] = pd.to_numeric(review_data[reviews], errors="coerce")
        ranked = review_data.dropna().sort_values(reviews, ascending=False)
        if not ranked.empty:
            insights.append(f"{ranked.iloc[0][product_name]} has the highest reported review count in this dataset ({int(ranked.iloc[0][reviews]):,}).")
    if not insights:
        insights.append("Beauty fields were detected, but more populated price, rating, or review values are needed for deeper product-performance analysis.")
    completeness = round((len(beauty_columns) / len(BEAUTY_COLUMNS)) * 100)
    return {"mode": "beauty", "profile": profile, "beauty_columns": beauty_columns, "completeness": completeness,
            "kpis": kpis[:6], "charts": charts[:6], "tables": tables, "insights": insights[:6]}


def generate_dashboard(data):
    beauty_columns = detect_beauty_columns(data)
    if len(beauty_columns) >= 2 and ("brand" in beauty_columns or "category" in beauty_columns):
        return generate_beauty_dashboard(data, beauty_columns)

    profile = profile_dataset(data)
    types = profile["types"]
    numeric = [name for name, kind in types.items() if kind == "Numeric"]
    categories = [name for name, kind in types.items() if kind == "Categorical"]
    dates = [name for name, kind in types.items() if kind == "Date"]
    kpis = [{"label": "Total Records", "value": f"{len(data):,}", "note": "Rows in cleaned dataset", "icon": "bi-table"},
            {"label": "Total Columns", "value": str(len(data.columns)), "note": "Detected fields", "icon": "bi-columns-gap"}]
    if numeric:
        kpis.append({"label": f"Average {numeric[0]}", "value": f"{_safe_number(data[numeric[0]].mean()):,}", "note": "Based on valid numeric values", "icon": "bi-calculator"})
    if categories:
        kpis.append({"label": f"{categories[0]} Groups", "value": str(data[categories[0]].nunique()), "note": "Unique categories", "icon": "bi-diagram-3"})
    charts, tables, insights = [], [], []
    for column in categories[:2]:
        counts = data[column].fillna("Unknown").value_counts().head(8)
        charts.append(_chart(f"Records by {column}", "bar", counts.index, counts.values))
        if not counts.empty:
            insights.append(f'"{counts.index[0]}" is the most frequent value in {column} ({int(counts.iloc[0]):,} records).')
    for column in numeric[:2]:
        values = data[column].dropna()
        if not values.empty:
            hist, edges = np.histogram(values, bins=min(8, max(3, values.nunique())))
            labels = [f"{edges[index]:.1f}–{edges[index + 1]:.1f}" for index in range(len(hist))]
            charts.append(_chart(f"Distribution of {column}", "bar", labels, hist))
            insights.append(f"{column} ranges from {_safe_number(values.min()):,} to {_safe_number(values.max()):,}, with an average of {_safe_number(values.mean()):,}.")
    if categories and numeric and len(charts) < 6:
        grouped = data.groupby(categories[0])[numeric[0]].mean().sort_values(ascending=False).head(8)
        charts.append(_chart(f"Average {numeric[0]} by {categories[0]}", "bar", grouped.index, grouped.values))
    if dates and numeric and len(charts) < 6:
        date_column, number_column = dates[0], numeric[0]
        temp = data[[date_column, number_column]].dropna().copy()
        temp[date_column] = pd.to_datetime(temp[date_column], errors="coerce")
        trend = temp.dropna().groupby(temp[date_column].dt.to_period("M"))[number_column].mean().tail(12)
        if not trend.empty:
            charts.append(_chart(f"Average {number_column} over time", "line", trend.index, trend.values))
    if len(numeric) >= 2 and len(charts) < 6:
        pair = data[[numeric[0], numeric[1]]].dropna().head(300)
        charts.append(_chart(f"{numeric[0]} compared with {numeric[1]}", "scatter", points=[{"x": _safe_number(x), "y": _safe_number(y)} for x, y in pair.values]))
    if numeric:
        rows = [{"column": column, "count": int(data[column].count()), "average": _safe_number(data[column].mean()),
                 "minimum": _safe_number(data[column].min()), "maximum": _safe_number(data[column].max())} for column in numeric[:6]]
        tables.append({"title": "Numeric summary", "kind": "numeric", "rows": rows})
    missing_rows = [{"column": name, "missing": int(data[name].isna().sum()), "percent": round(data[name].isna().mean() * 100, 1)} for name in data.columns if data[name].isna().sum()]
    if missing_rows:
        missing_rows.sort(key=lambda item: item["missing"], reverse=True)
        tables.append({"title": "Missing value summary", "kind": "missing", "rows": missing_rows[:8]})
    if not insights:
        insights.append("The dataset has been profiled successfully. Add numeric, category, or date fields for deeper comparisons.")
    return {"mode": "generic", "profile": profile, "kpis": kpis[:4], "charts": charts[:6], "tables": tables[:3], "insights": insights[:6]}
