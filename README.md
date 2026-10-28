# DataLens Beauty – Consumer Buying Behavior & Product Performance Analysis

DataLens Beauty is a Flask mini-project for beauty-industry analytics. It supports two connected workflows: upload a structured CSV/Excel dataset for analysis, or explore available product information from Open Beauty Facts. The upload engine remains generic and works with other structured datasets too.

## Features

- Secure register, login, logout, bcrypt password hashing, and protected pages
- CSV, XLSX, and XLS upload validation with configurable size, row, and column limits
- Automatic detection of numeric, categorical, text, date, boolean, and ID-like columns
- Clear data profile with missing values, unique counts, and duplicates
- Explainable cleaning: empty rows/columns, duplicates, text trimming, numeric/date conversion, and careful missing-value handling
- Dynamic KPIs, Chart.js charts, summary tables, and rule-based insights created from uploaded values
- MySQL-backed dataset and analysis history, limited to the signed-in user
- Responsive Bootstrap dashboard with mobile sidebar behavior
- Open Beauty Facts product explorer with barcode lookup, structured brand/category search, cached product details, and API image fallbacks
- Beauty-aware uploaded-dataset mode with product, price, rating, review, category, and brand detection

## Technology stack

HTML5, CSS3, Bootstrap 5, vanilla JavaScript, Chart.js, Python, Flask, Pandas, NumPy, openpyxl, MySQL, bcrypt, and python-dotenv.

## Architecture

`Browser → Flask routes → Pandas analytics helpers → MySQL`

The browser renders values supplied by Flask. Pandas performs profiling, cleaning, and summaries; JavaScript only handles UI behavior and rendering Chart.js charts.

For the beauty explorer, the flow is `Browser → Flask → Open Beauty Facts → normalized product data → MySQL cache → templates`.

## Folder structure

```
data_analysis(proj)/
├── app.py                 # Flask routes and authentication
├── analytics.py           # Dynamic profiling, cleaning, and analysis
├── beauty_api.py          # Open Beauty Facts API client and normalization
├── config.py              # Environment configuration
├── database/schema.sql    # MySQL tables
├── database/migration_beauty.sql # Update script for an existing database
├── sample_data/           # Small test CSV files
├── static/css/style.css
├── static/js/
├── templates/
├── uploads/               # Temporary uploaded files (created/used at runtime)
├── requirements.txt
└── .env.example
```

## Installation and running

1. Install Python 3.10+ and MySQL Server.
2. Create a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Create the MySQL database and tables. Run `database/schema.sql` in MySQL Workbench, or use:

   ```powershell
   mysql -u root -p < database/schema.sql
   ```

4. Copy `.env.example` to `.env`, then enter your actual MySQL password and a long secret key.
   If you already created the database before the beauty update, run `database/migration_beauty.sql` once as well.
5. Start the app:

   ```powershell
   python app.py
   ```

6. Open `http://127.0.0.1:5000`, register an account, and upload a dataset.

## Dataset requirements

The first row must contain unique column names. Files must be structured, tabular CSV or Excel data—not a decorative report with merged headings, images, and unrelated sections. Default limits are 10 MB, 50,000 rows, and 100 columns; change them in `.env` if needed.

Try `sample_data/sample_sales.csv`, `sample_data/sample_students.csv`, or `sample_data/sample_employees.csv`. They are only testing data, not special cases in the application.

Use `sample_data/beauty_products_5000.csv` to test Beauty Industry Analytics mode. It contains beauty-related fields including product name, brand, category, price, rating, and review count.

## How dynamic analysis works

DataLens inspects each column. Numeric values receive descriptive statistics and distributions; repeated short text values become categories; date-like values become time fields; highly unique identifiers become ID-like fields. It then limits the dashboard to useful comparisons such as category counts, category-plus-number averages, numeric distributions, time trends, and numeric scatter plots.

When beauty fields are detected flexibly (for example `Brand`, `Product Category`, `Price_INR`, `Rating`, or `Review_Count`), the dashboard shows beauty-specific cards and charts. Ratings and review volume are presented as product information or consumer preference indicators, not actual sales or purchase behavior.

## Beauty product explorer

Log in and open **Explore Beauty Products**. Search by barcode for an exact product, or use product keyword, brand, or category filters. The server calls Open Beauty Facts with a custom User-Agent, keeps only the fields used by the pages, and stores barcode-based products in the `beauty_products` table without creating duplicates.

Open Beauty Facts does not guarantee price, rating, review count, images, ingredients, or any sales information. DataLens Beauty displays unavailable fields as `Not available` and never converts ratings or review counts into sales claims.

## Testing checklist

- Register, login, invalid login, duplicate email, logout, and protected routes
- Upload each sample CSV and a structured XLSX file
- Reject an EXE/TXT file, an empty file, and malformed CSV/Excel data
- Try missing values, duplicate rows, numeric/date/category fields, and 3+ / 20+ column datasets
- Confirm the profile, cleaning report, dashboard KPIs, charts, insights, and history use the uploaded data
- Test the mobile layout and 404 page

## Common issues

**MySQL connection error:** Ensure MySQL is running, import `database/schema.sql`, and check `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` in `.env`.

**Excel upload error:** Install packages from `requirements.txt`; `openpyxl` reads XLSX files. Old XLS files may require an additional compatible Excel reader depending on your Python environment.

**File rejected:** Ensure the file is CSV/XLSX/XLS, has headers and data rows, and is within the configured limits.

## Viva summary

Flask provides routes and sessions. bcrypt hashes passwords before MySQL storage. Uploads use secure filenames and are read by Pandas. `analytics.py` detects generic data types, profiles data, applies cautious cleaning rules, and returns dictionaries for templates. Chart.js receives only summarized chart points, so the browser is not sent the entire dataset. MySQL holds user accounts, upload metadata, and profile history rather than spreadsheet files.
