CREATE DATABASE IF NOT EXISTS cafeteria_virtual
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cafeteria_virtual;

CREATE TABLE IF NOT EXISTS user (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(30) NOT NULL DEFAULT 'usuario',
  points INT NOT NULL DEFAULT 0
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
  points_earned INT NOT NULL DEFAULT 0,
  points_redeemed INT NOT NULL DEFAULT 0,
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

CREATE TABLE IF NOT EXISTS points_transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  order_id INT NULL,
  points_changed INT NOT NULL,
  type ENUM('gain','redeem') NOT NULL,
  description VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_points_user FOREIGN KEY (user_id) REFERENCES user(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_points_order FOREIGN KEY (order_id) REFERENCES `order`(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dining_table (
  id INT AUTO_INCREMENT PRIMARY KEY,
  table_number VARCHAR(20) NOT NULL UNIQUE,
  capacity INT NOT NULL DEFAULT 4,
  location_note VARCHAR(255) NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dine_in_order (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL UNIQUE,
  table_id INT NOT NULL,
  waiter_id INT NOT NULL,
  cashier_id INT NULL,
  customer_name_snapshot VARCHAR(120) NOT NULL,
  payment_method ENUM('efectivo', 'tarjeta') NOT NULL,
  status VARCHAR(80) NOT NULL DEFAULT 'confirmado',
  sent_to_cash_at DATETIME NULL,
  sent_to_kitchen_at DATETIME NULL,
  ready_at DATETIME NULL,
  delivered_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_dine_in_order_order FOREIGN KEY (order_id) REFERENCES `order`(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_dine_in_order_table FOREIGN KEY (table_id) REFERENCES dining_table(id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_dine_in_order_waiter FOREIGN KEY (waiter_id) REFERENCES user(id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_dine_in_order_cashier FOREIGN KEY (cashier_id) REFERENCES user(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS delivery_order (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL UNIQUE,
  courier_id INT NULL,
  customer_name_snapshot VARCHAR(120) NOT NULL,
  delivery_address TEXT NOT NULL,
  delivery_distance_km DECIMAL(10,2) NOT NULL DEFAULT 0,
  delivery_fee DOUBLE NOT NULL DEFAULT 0,
  route_map_data LONGTEXT NULL,
  payment_method ENUM('efectivo', 'tarjeta') NOT NULL,
  cash_on_delivery BOOLEAN NOT NULL DEFAULT FALSE,
  payment_status ENUM('pendiente', 'confirmado', 'pagado', 'rechazado') NOT NULL DEFAULT 'pendiente',
  status VARCHAR(80) NOT NULL DEFAULT 'confirmado',
  sent_to_kitchen_at DATETIME NULL,
  ready_at DATETIME NULL,
  delivered_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_delivery_order_order FOREIGN KEY (order_id) REFERENCES `order`(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_delivery_order_courier FOREIGN KEY (courier_id) REFERENCES user(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS order_status_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  service_type ENUM('presencial', 'domicilio') NOT NULL,
  status VARCHAR(80) NOT NULL,
  actor_role VARCHAR(30) NOT NULL,
  actor_user_id INT NULL,
  notes VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_order_status_history_order FOREIGN KEY (order_id) REFERENCES `order`(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_order_status_history_actor FOREIGN KEY (actor_user_id) REFERENCES user(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Los usuarios admin@x.com y cocina@x.com los crea automáticamente la app al arrancar.