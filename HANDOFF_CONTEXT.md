# DataLens Project Handoff Context

## Project goal

DataLens is a college mini-project: a Flask web app that accepts any structured CSV/Excel dataset, profiles it, cleans it carefully, and generates dynamic KPIs, Chart.js visualizations, tables, and rule-based insights. It must not depend on fixed domains such as products, sales, employees, or students.

## Current stack

- Frontend: HTML, CSS, Bootstrap 5, vanilla JavaScript, Chart.js
- Backend: Python and Flask
- Data processing: Pandas, NumPy, openpyxl
- Database: MySQL with mysql-connector-python
- Authentication: Flask sessions and bcrypt password hashing

## What is already implemented

1. Landing page with DataLens brand and externally hosted analytics photo.
2. Register, login, logout, bcrypt password hashing, duplicate-email validation, and protected user pages.
3. Password show/hide eye buttons on login and registration.
4. CSV/XLSX/XLS upload with secure filename handling, size limits, row/column limits, and structured-data validation.
5. Generic type detection for Numeric, Categorical, Text, Date, Boolean, and ID-like fields.
6. Data profile page with dataset overview and per-column details.
7. Cleaning preview and apply flow: removes empty rows/columns and duplicates, trims strings, converts types, and fills suitable missing values.
8. Dynamic dashboard KPIs, tables, rule-based insights, and Chart.js visualizations based on detected types.
9. Interactive charts: hover tooltips, click-to-inspect details, Bar/Line/Doughnut switching, and expand view.
10. MySQL schema for users, datasets, and analysis_history, plus user-specific history pages.
11. Sample datasets, including beauty_products_5000.csv with 5,025 records, 20 fields, 25 intentional duplicate records, and selected missing values.

## Important design rules

- Do not hard-code analysis around beauty products, sales, employees, students, or any other domain.
- All dashboard KPIs, charts, and insights must come from actual uploaded data.
- Keep the code simple and easy for a B.Sc. Computer Science student to explain in viva.
- Do not replace Flask/MySQL/Pandas/Chart.js with another framework.
- Do not add fake data or fake buttons.

## Current routes

- `/` landing page
- `/register`, `/login`, `/logout`
- `/dashboard`, `/upload`, `/data-profile`, `/cleaning`, `/analysis`
- `/history`, `/history/<dataset_id>`

## Current database tables

- `users`: id, name, email, password, created_at
- `datasets`: id, user_id, file_name, file_type, row_count, column_count, uploaded_at
- `analysis_history`: id, dataset_id, summary_data, created_at

## Current limitation: admin functionality has not been implemented

The user is now writing backend code themselves and has asked for guidance only, not generated code or direct edits.

There is currently no `role` column, no admin routes, and no admin templates. The recommended next implementation order is:

1. Add a `role` field to `users` with `customer` as the default.
2. Make the user’s own account an `admin` directly in MySQL Workbench.
3. During login, store `user_id`, `user_name`, and `user_role` in session.
4. Redirect admin users to an admin dashboard and customers to the existing dashboard.
5. Make an admin-only access check.
6. Build only three admin pages first: admin dashboard, user list, and all-datasets list.

## 7-day work plan previously agreed

- Day 1: User roles, login redirect, and role protection.
- Day 2: Admin dashboard with real MySQL counts.
- Day 3: Manage users page.
- Day 4: Manage datasets page using users/datasets join.
- Day 5: Test/fix the complete customer flow.
- Day 6: Improve UI responsiveness and error handling.
- Day 7: Final testing, screenshots, README update, and viva practice.

## How to run

1. Create and activate a Python virtual environment.
2. Run `pip install -r requirements.txt`.
3. Run `database/schema.sql` in MySQL Workbench.
4. Copy `.env.example` to `.env` and enter local MySQL credentials.
5. Run `python app.py`.
6. Open `http://127.0.0.1:5000`.

## Notes for the next assistant

- Inspect the current project before recommending changes because the student may edit files after this handoff.
- Preserve the simple student-friendly architecture.
- The user prefers step-by-step guidance and may explicitly ask not to generate code or modify files. Respect that request.
- Do not expose `.env` values or package `.env` in a shared archive.
