-- Схема PostgreSQL для MVP банковских сообществ
-- Связь с Neo4j: client.id = (:User {id})
-- community.category_key = p.category_key в Neo4j (MCC-группа)

CREATE TABLE IF NOT EXISTS client (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    login VARCHAR(50) UNIQUE,
    password VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS community (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    category_key VARCHAR(64),
    min_transactions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE community ADD COLUMN IF NOT EXISTS category_key VARCHAR(64);
ALTER TABLE community ADD COLUMN IF NOT EXISTS min_transactions INTEGER DEFAULT 0;

CREATE TABLE IF NOT EXISTS client_community (
    id_client INT NOT NULL,
    id_community INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (id_client, id_community),
    FOREIGN KEY (id_client) REFERENCES client(id) ON DELETE CASCADE,
    FOREIGN KEY (id_community) REFERENCES community(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS post (
    id SERIAL PRIMARY KEY,
    id_sender INT NOT NULL,
    id_community INT NOT NULL,
    title VARCHAR(225),
    text TEXT,
    image_url VARCHAR(255),
    rating INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (id_sender) REFERENCES client(id) ON DELETE CASCADE,
    FOREIGN KEY (id_community) REFERENCES community(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS post_like (
    id_client INT NOT NULL,
    id_post INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id_client, id_post),
    FOREIGN KEY (id_client) REFERENCES client(id) ON DELETE CASCADE,
    FOREIGN KEY (id_post) REFERENCES post(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comment (
    id SERIAL PRIMARY KEY,
    id_post INT NOT NULL,
    id_sender INT NOT NULL,
    id_parent INT,
    message TEXT,
    rating INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (id_post) REFERENCES post(id) ON DELETE CASCADE,
    FOREIGN KEY (id_sender) REFERENCES client(id) ON DELETE CASCADE,
    FOREIGN KEY (id_parent) REFERENCES comment(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS cashback (
    id SERIAL PRIMARY KEY,
    amount FLOAT,
    place INT,
    category_key VARCHAR(64),
    category_label VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE cashback ADD COLUMN IF NOT EXISTS category_key VARCHAR(64);
ALTER TABLE cashback ADD COLUMN IF NOT EXISTS category_label VARCHAR(120);

CREATE TABLE IF NOT EXISTS client_cashback (
    id_client INT NOT NULL,
    id_cashback INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (id_client, id_cashback),
    FOREIGN KEY (id_client) REFERENCES client(id) ON DELETE CASCADE,
    FOREIGN KEY (id_cashback) REFERENCES cashback(id) ON DELETE CASCADE
);

-- Предложения «Выгода»: активны, если пользователь в сообществе
CREATE TABLE IF NOT EXISTS cashback_offer (
    id SERIAL PRIMARY KEY,
    id_community INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    percent INT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (id_community) REFERENCES community(id) ON DELETE CASCADE
);
