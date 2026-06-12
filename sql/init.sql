-- =====================================================================
-- Lược đồ cơ sở dữ liệu Hệ thống Quản lý Kho hàng
-- (Tham khảo - hệ thống sử dụng SQLite, schema được tạo tự động trong
--  src/warehouse/database/database.py. Tệp này dùng để minh họa thiết kế.)
-- =====================================================================

-- Bảng người dùng
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('MANAGER', 'STAFF')),
    full_name     TEXT    NOT NULL DEFAULT '',
    email         TEXT    NOT NULL DEFAULT '',
    department    TEXT    NOT NULL DEFAULT '',
    position      TEXT    NOT NULL DEFAULT '',
    phone         TEXT    NOT NULL DEFAULT '',
    bio           TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng nhà cung cấp
CREATE TABLE IF NOT EXISTS suppliers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    code           TEXT    NOT NULL UNIQUE,
    name           TEXT    NOT NULL,
    contact_person TEXT    NOT NULL DEFAULT '',
    phone          TEXT    NOT NULL DEFAULT '',
    email          TEXT    NOT NULL DEFAULT '',
    address        TEXT    NOT NULL DEFAULT '',
    status         TEXT    NOT NULL DEFAULT 'ACTIVE'
                   CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng hàng hóa
CREATE TABLE IF NOT EXISTS products (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sku          TEXT    NOT NULL UNIQUE,
    name         TEXT    NOT NULL,
    category     TEXT    NOT NULL DEFAULT '',
    unit         TEXT    NOT NULL DEFAULT 'cái',
    quantity     INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    min_quantity INTEGER NOT NULL DEFAULT 0 CHECK (min_quantity >= 0),
    unit_price   REAL    NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
    location     TEXT    NOT NULL DEFAULT '',
    supplier_id  INTEGER,
    status       TEXT    NOT NULL DEFAULT 'ACTIVE'
                 CHECK (status IN ('ACTIVE', 'DISCONTINUED')),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id) ON DELETE SET NULL
);

-- Bảng giao dịch nhập/xuất kho
CREATE TABLE IF NOT EXISTS transactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    code             TEXT    NOT NULL UNIQUE,
    type             TEXT    NOT NULL CHECK (type IN ('IMPORT', 'EXPORT')),
    product_id       INTEGER NOT NULL,
    product_name     TEXT    NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    unit_price       REAL    NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
    total            REAL    NOT NULL DEFAULT 0 CHECK (total >= 0),
    partner          TEXT    NOT NULL DEFAULT '',
    user_username    TEXT    NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    note             TEXT    NOT NULL DEFAULT '',
    FOREIGN KEY (product_id)    REFERENCES products (id),
    FOREIGN KEY (user_username) REFERENCES users (username)
);

-- Chỉ mục tối ưu truy vấn
CREATE INDEX IF NOT EXISTS idx_tx_product       ON transactions (product_id);
CREATE INDEX IF NOT EXISTS idx_tx_type          ON transactions (type);
CREATE INDEX IF NOT EXISTS idx_tx_date          ON transactions (transaction_date);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
