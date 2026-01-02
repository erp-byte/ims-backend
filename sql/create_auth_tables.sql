-- =====================================================
-- Authentication System Database Tables
-- PostgreSQL DDL Queries
-- =====================================================

-- =====================================================
-- 1. IMS Users Table
-- =====================================================
CREATE TABLE IF NOT EXISTS ims_users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create indexes for ims_users
CREATE INDEX IF NOT EXISTS idx_user_username ON ims_users(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON ims_users(email);
CREATE INDEX IF NOT EXISTS idx_user_active ON ims_users(is_active);

-- Create updated_at trigger function if not exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for ims_users
DROP TRIGGER IF EXISTS update_ims_users_updated_at ON ims_users;
CREATE TRIGGER update_ims_users_updated_at
    BEFORE UPDATE ON ims_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE ims_users IS 'User authentication and management table';
COMMENT ON COLUMN ims_users.password_hash IS 'Bcrypt hashed password (cost factor: 12)';
COMMENT ON COLUMN ims_users.is_superuser IS 'Superuser has all permissions across all modules';


-- =====================================================
-- 2. Modules Table
-- =====================================================
CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add display_name column if it doesn't exist (for existing tables)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'modules' AND column_name = 'display_name'
    ) THEN
        ALTER TABLE modules ADD COLUMN display_name VARCHAR(100);
        -- Set default values for existing rows
        UPDATE modules SET display_name = INITCAP(name) WHERE display_name IS NULL;
        -- Make it NOT NULL after setting values
        ALTER TABLE modules ALTER COLUMN display_name SET NOT NULL;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'modules' AND column_name = 'description'
    ) THEN
        ALTER TABLE modules ADD COLUMN description VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'modules' AND column_name = 'is_active'
    ) THEN
        ALTER TABLE modules ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'modules' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE modules ADD COLUMN created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'modules' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE modules ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
    END IF;
END $$;

-- Create indexes for modules
CREATE INDEX IF NOT EXISTS idx_module_name ON modules(name);

-- Create trigger for modules
DROP TRIGGER IF EXISTS update_modules_updated_at ON modules;
CREATE TRIGGER update_modules_updated_at
    BEFORE UPDATE ON modules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE modules IS 'System modules (purchase, transfers, rtv, sales, printing)';


-- =====================================================
-- 3. User-Modules Association Table (Many-to-Many)
-- =====================================================
CREATE TABLE IF NOT EXISTS user_modules (
    user_id BIGINT NOT NULL,
    module_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, module_id),
    FOREIGN KEY (user_id) REFERENCES ims_users(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);

-- Create indexes for user_modules
CREATE INDEX IF NOT EXISTS idx_user_modules_user ON user_modules(user_id);
CREATE INDEX IF NOT EXISTS idx_user_modules_module ON user_modules(module_id);

COMMENT ON TABLE user_modules IS 'Many-to-many relationship between users and modules';


-- =====================================================
-- 4. Purchase Permissions Table
-- =====================================================
CREATE TABLE IF NOT EXISTS purchase_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    can_create BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit BOOLEAN NOT NULL DEFAULT FALSE,
    can_approve BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    can_view BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES ims_users(id) ON DELETE CASCADE,
    CONSTRAINT uq_purchase_permission_user UNIQUE (user_id)
);

-- Create indexes for purchase_permissions
CREATE INDEX IF NOT EXISTS idx_purchase_perm_user ON purchase_permissions(user_id);

-- Create trigger for purchase_permissions
DROP TRIGGER IF EXISTS update_purchase_permissions_updated_at ON purchase_permissions;
CREATE TRIGGER update_purchase_permissions_updated_at
    BEFORE UPDATE ON purchase_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE purchase_permissions IS 'Permissions for purchase module';


-- =====================================================
-- 5. Transfer Permissions Table
-- =====================================================
CREATE TABLE IF NOT EXISTS transfer_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    can_create BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit BOOLEAN NOT NULL DEFAULT FALSE,
    can_approve BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    can_view BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES ims_users(id) ON DELETE CASCADE,
    CONSTRAINT uq_transfer_permission_user UNIQUE (user_id)
);

-- Create indexes for transfer_permissions
CREATE INDEX IF NOT EXISTS idx_transfer_perm_user ON transfer_permissions(user_id);

-- Create trigger for transfer_permissions
DROP TRIGGER IF EXISTS update_transfer_permissions_updated_at ON transfer_permissions;
CREATE TRIGGER update_transfer_permissions_updated_at
    BEFORE UPDATE ON transfer_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE transfer_permissions IS 'Permissions for transfer module';


-- =====================================================
-- 6. RTV Permissions Table
-- =====================================================
CREATE TABLE IF NOT EXISTS rtv_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    can_create BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit BOOLEAN NOT NULL DEFAULT FALSE,
    can_approve BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    can_view BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES ims_users(id) ON DELETE CASCADE,
    CONSTRAINT uq_rtv_permission_user UNIQUE (user_id)
);

-- Create indexes for rtv_permissions
CREATE INDEX IF NOT EXISTS idx_rtv_perm_user ON rtv_permissions(user_id);

-- Create trigger for rtv_permissions
DROP TRIGGER IF EXISTS update_rtv_permissions_updated_at ON rtv_permissions;
CREATE TRIGGER update_rtv_permissions_updated_at
    BEFORE UPDATE ON rtv_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE rtv_permissions IS 'Permissions for RTV (Return to Vendor) module';


-- =====================================================
-- 7. Sales Permissions Table
-- =====================================================
CREATE TABLE IF NOT EXISTS sales_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    can_create BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit BOOLEAN NOT NULL DEFAULT FALSE,
    can_approve BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    can_view BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES ims_users(id) ON DELETE CASCADE,
    CONSTRAINT uq_sales_permission_user UNIQUE (user_id)
);

-- Create indexes for sales_permissions
CREATE INDEX IF NOT EXISTS idx_sales_perm_user ON sales_permissions(user_id);

-- Create trigger for sales_permissions
DROP TRIGGER IF EXISTS update_sales_permissions_updated_at ON sales_permissions;
CREATE TRIGGER update_sales_permissions_updated_at
    BEFORE UPDATE ON sales_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sales_permissions IS 'Permissions for sales module';


-- =====================================================
-- 8. Printing Permissions Table
-- =====================================================
CREATE TABLE IF NOT EXISTS printing_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    can_create BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit BOOLEAN NOT NULL DEFAULT FALSE,
    can_approve BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    can_view BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES ims_users(id) ON DELETE CASCADE,
    CONSTRAINT uq_printing_permission_user UNIQUE (user_id)
);

-- Create indexes for printing_permissions
CREATE INDEX IF NOT EXISTS idx_printing_perm_user ON printing_permissions(user_id);

-- Create trigger for printing_permissions
DROP TRIGGER IF EXISTS update_printing_permissions_updated_at ON printing_permissions;
CREATE TRIGGER update_printing_permissions_updated_at
    BEFORE UPDATE ON printing_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE printing_permissions IS 'Permissions for printing module';


-- =====================================================
-- Insert Default Modules
-- =====================================================
DO $$
BEGIN
    -- Insert modules only if they don't exist
    IF NOT EXISTS (SELECT 1 FROM modules WHERE name = 'purchase') THEN
        INSERT INTO modules (name, display_name, description) VALUES ('purchase', 'Purchase', 'Purchase Order Management');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM modules WHERE name = 'transfers') THEN
        INSERT INTO modules (name, display_name, description) VALUES ('transfers', 'Transfers', 'Inventory Transfer Management');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM modules WHERE name = 'rtv') THEN
        INSERT INTO modules (name, display_name, description) VALUES ('rtv', 'RTV', 'Return to Vendor Management');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM modules WHERE name = 'sales') THEN
        INSERT INTO modules (name, display_name, description) VALUES ('sales', 'Sales', 'Sales Order Management');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM modules WHERE name = 'printing') THEN
        INSERT INTO modules (name, display_name, description) VALUES ('printing', 'Printing', 'Label and Document Printing');
    END IF;
END $$;


-- =====================================================
-- Create Default Superuser
-- Password: admin123 (Bcrypt hash)
-- ⚠️ CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!
-- =====================================================
-- Note: The password hash below is for "admin123"
-- Generated using Bcrypt with cost factor 12
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM ims_users WHERE username = 'admin') THEN
        INSERT INTO ims_users (username, password_hash, email, full_name, is_active, is_superuser) 
        VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeUuL.HLtG8a', 'admin@candorfoods.com', 'System Administrator', TRUE, TRUE);
    END IF;
END $$;


-- =====================================================
-- Assign All Modules to Superuser
-- =====================================================
DO $$
DECLARE
    admin_user_id BIGINT;
    module_record RECORD;
BEGIN
    -- Get admin user ID
    SELECT id INTO admin_user_id FROM ims_users WHERE username = 'admin';
    
    IF admin_user_id IS NOT NULL THEN
        -- Assign all modules to admin
        FOR module_record IN SELECT id FROM modules LOOP
            IF NOT EXISTS (
                SELECT 1 FROM user_modules 
                WHERE user_id = admin_user_id AND module_id = module_record.id
            ) THEN
                INSERT INTO user_modules (user_id, module_id) 
                VALUES (admin_user_id, module_record.id);
            END IF;
        END LOOP;
    END IF;
END $$;


-- =====================================================
-- Verification Queries
-- =====================================================

-- Check if all tables were created
SELECT 
    table_name 
FROM 
    information_schema.tables 
WHERE 
    table_schema = 'public' 
    AND table_name IN (
        'ims_users', 
        'modules', 
        'user_modules', 
        'purchase_permissions', 
        'transfer_permissions', 
        'rtv_permissions', 
        'sales_permissions', 
        'printing_permissions'
    )
ORDER BY 
    table_name;

-- Verify default modules
SELECT * FROM modules ORDER BY id;

-- Verify default admin user
SELECT 
    id, 
    username, 
    email, 
    full_name, 
    is_active, 
    is_superuser, 
    created_at 
FROM 
    ims_users 
WHERE 
    username = 'admin';

-- Verify admin has all modules
SELECT 
    u.username,
    m.name AS module_name,
    m.display_name
FROM 
    ims_users u
    JOIN user_modules um ON u.id = um.user_id
    JOIN modules m ON um.module_id = m.id
WHERE 
    u.username = 'admin'
ORDER BY 
    m.name;


-- =====================================================
-- Useful Queries for Management
-- =====================================================

-- Get all users with their modules
SELECT 
    u.id,
    u.username,
    u.email,
    u.is_superuser,
    u.is_active,
    STRING_AGG(m.name, ', ' ORDER BY m.name) AS modules
FROM 
    ims_users u
    LEFT JOIN user_modules um ON u.id = um.user_id
    LEFT JOIN modules m ON um.module_id = m.id
GROUP BY 
    u.id, u.username, u.email, u.is_superuser, u.is_active
ORDER BY 
    u.id;


-- Get user permissions across all modules
SELECT 
    u.username,
    'purchase' AS module,
    pp.can_create, pp.can_edit, pp.can_approve, pp.can_delete, pp.can_view
FROM 
    ims_users u
    LEFT JOIN purchase_permissions pp ON u.id = pp.user_id
WHERE 
    u.username = 'admin'  -- Change username as needed

UNION ALL

SELECT 
    u.username,
    'transfers' AS module,
    tp.can_create, tp.can_edit, tp.can_approve, tp.can_delete, tp.can_view
FROM 
    ims_users u
    LEFT JOIN transfer_permissions tp ON u.id = tp.user_id
WHERE 
    u.username = 'admin'

UNION ALL

SELECT 
    u.username,
    'rtv' AS module,
    rp.can_create, rp.can_edit, rp.can_approve, rp.can_delete, rp.can_view
FROM 
    ims_users u
    LEFT JOIN rtv_permissions rp ON u.id = rp.user_id
WHERE 
    u.username = 'admin'

UNION ALL

SELECT 
    u.username,
    'sales' AS module,
    sp.can_create, sp.can_edit, sp.can_approve, sp.can_delete, sp.can_view
FROM 
    ims_users u
    LEFT JOIN sales_permissions sp ON u.id = sp.user_id
WHERE 
    u.username = 'admin'

UNION ALL

SELECT 
    u.username,
    'printing' AS module,
    prp.can_create, prp.can_edit, prp.can_approve, prp.can_delete, prp.can_view
FROM 
    ims_users u
    LEFT JOIN printing_permissions prp ON u.id = prp.user_id
WHERE 
    u.username = 'admin';


-- =====================================================
-- Clean Up / Drop All Tables (Use with caution!)
-- =====================================================
-- Uncomment below to drop all authentication tables

/*
DROP TABLE IF EXISTS printing_permissions CASCADE;
DROP TABLE IF EXISTS sales_permissions CASCADE;
DROP TABLE IF EXISTS rtv_permissions CASCADE;
DROP TABLE IF EXISTS transfer_permissions CASCADE;
DROP TABLE IF EXISTS purchase_permissions CASCADE;
DROP TABLE IF EXISTS user_modules CASCADE;
DROP TABLE IF EXISTS modules CASCADE;
DROP TABLE IF EXISTS ims_users CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
*/
