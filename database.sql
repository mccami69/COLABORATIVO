CREATE DATABASE IF NOT EXISTS cafeteria_virtual
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cafeteria_virtual;

CREATE TABLE IF NOT EXISTS user (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(30) NOT NULL DEFAULT 'usuario'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS product (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(140) NOT NULL,
  description TEXT NOT NULL,
  category VARCHAR(60) NOT NULL,
  image_url TEXT NOT NULL,
  price DOUBLE NOT NULL,
  discount_price DOUBLE NULL,
  ingredients TEXT NOT NULL,
  ingredient_options TEXT NOT NULL,
  exhausted BOOLEAN NOT NULL DEFAULT FALSE,
  sold_count INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inventory_item (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(140) NOT NULL,
  price DOUBLE NOT NULL,
  units DOUBLE NOT NULL,
  quantity DOUBLE NOT NULL,
  unit_type VARCHAR(40) NOT NULL,
  unit_value DOUBLE NOT NULL,
  sale_value DOUBLE NOT NULL,
  profit DOUBLE NOT NULL,
  total DOUBLE NOT NULL,
  expiration_date VARCHAR(40) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `order` (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  status VARCHAR(80) NOT NULL DEFAULT 'pedido confirmado',
  payment_method VARCHAR(30) NOT NULL,
  dining_option VARCHAR(30) NOT NULL,
  total DOUBLE NOT NULL,
  kitchen_done BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_order_user FOREIGN KEY (user_id) REFERENCES user(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS order_item (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NULL,
  name_snapshot VARCHAR(140) NOT NULL,
  price_snapshot DOUBLE NOT NULL,
  quantity INT NOT NULL,
  ingredient_notes TEXT NOT NULL,
  CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES `order`(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_order_item_product FOREIGN KEY (product_id) REFERENCES product(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Los usuarios admin@x.com y cocina@x.com los crea automáticamente la app al arrancar.