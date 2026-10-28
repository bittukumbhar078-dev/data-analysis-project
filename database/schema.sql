CREATE DATABASE IF NOT EXISTS datalens;
USE datalens;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    row_count INT NOT NULL,
    column_count INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analysis_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    summary_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS beauty_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    external_product_id VARCHAR(100),
    barcode VARCHAR(100) UNIQUE,
    product_name VARCHAR(255),
    brand VARCHAR(255),
    category VARCHAR(255),
    price DECIMAL(10,2) NULL,
    rating DECIMAL(3,2) NULL,
    review_count INT NULL,
    description TEXT,
    image_url TEXT,
    ingredients TEXT,
    quantity VARCHAR(100),
    countries TEXT,
    source VARCHAR(100) NOT NULL DEFAULT 'Open Beauty Facts',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_product_name (product_name),
    INDEX idx_brand (brand),
    INDEX idx_category (category)
);
