USE datalens;

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
