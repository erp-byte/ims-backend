-- =====================================================
-- Sample Queries for Authentication System
-- Common operations and examples
-- =====================================================

-- =====================================================
-- 1. USER MANAGEMENT QUERIES
-- =====================================================

-- Create a new user (manual SQL - normally done via API)
-- Note: Password must be hashed using Bcrypt before inserting
INSERT INTO ims_users (username, password_hash, email, full_name, is_active, is_superuser)
VALUES (
    'john_doe',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeUuL.HLtG8a', -- This is "admin123" - should be replaced
    'john@example.com',
    'John Doe',
    TRUE,
    FALSE
);

-- Get user by username
SELECT * FROM ims_users WHERE username = 'john_doe';

-- Get user by email
SELECT * FROM ims_users WHERE email = 'john@example.com';

-- Get all active users
SELECT 
    id, 
    username, 
    email, 
    full_name, 
    is_superuser, 
    last_login 
FROM 
    ims_users 
WHERE 
    is_active = TRUE
ORDER BY 
    created_at DESC;

-- Update user information
UPDATE ims_users 
SET 
    email = 'newemail@example.com',
    full_name = 'John Updated Doe',
    updated_at = NOW()
WHERE 
    username = 'john_doe';

-- Deactivate user (soft delete)
UPDATE ims_users 
SET 
    is_active = FALSE,
    updated_at = NOW()
WHERE 
    username = 'john_doe';

-- Reactivate user
UPDATE ims_users 
SET 
    is_active = TRUE,
    updated_at = NOW()
WHERE 
    username = 'john_doe';

-- Delete user (hard delete - cascades to permissions and modules)
DELETE FROM ims_users WHERE username = 'john_doe';

-- Update last login timestamp
UPDATE ims_users 
SET 
    last_login = NOW()
WHERE 
    username = 'john_doe';

-- Change user password (requires Bcrypt hash)
UPDATE ims_users 
SET 
    password_hash = '$2b$12$NEW_BCRYPT_HASH_HERE',
    updated_at = NOW()
WHERE 
    username = 'john_doe';


-- =====================================================
-- 2. MODULE MANAGEMENT QUERIES
-- =====================================================

-- Get all active modules
SELECT * FROM modules WHERE is_active = TRUE ORDER BY name;

-- Get specific module
SELECT * FROM modules WHERE name = 'purchase';

-- Add a new module (if needed in future)
INSERT INTO modules (name, display_name, description)
VALUES ('inventory', 'Inventory', 'Inventory Management');

-- Deactivate a module
UPDATE modules 
SET 
    is_active = FALSE,
    updated_at = NOW()
WHERE 
    name = 'printing';


-- =====================================================
-- 3. USER-MODULE ASSIGNMENT QUERIES
-- =====================================================

-- Assign a module to a user
INSERT INTO user_modules (user_id, module_id)
VALUES (
    (SELECT id FROM ims_users WHERE username = 'john_doe'),
    (SELECT id FROM modules WHERE name = 'purchase')
);

-- Assign multiple modules to a user
INSERT INTO user_modules (user_id, module_id)
SELECT 
    (SELECT id FROM ims_users WHERE username = 'john_doe'),
    id
FROM 
    modules
WHERE 
    name IN ('purchase', 'sales', 'transfers');

-- Remove a module from a user
DELETE FROM user_modules
WHERE 
    user_id = (SELECT id FROM ims_users WHERE username = 'john_doe')
    AND module_id = (SELECT id FROM modules WHERE name = 'printing');

-- Get all modules assigned to a user
SELECT 
    m.id,
    m.name,
    m.display_name,
    m.description
FROM 
    modules m
    JOIN user_modules um ON m.id = um.module_id
WHERE 
    um.user_id = (SELECT id FROM ims_users WHERE username = 'john_doe')
ORDER BY 
    m.name;

-- Get all users with a specific module
SELECT 
    u.id,
    u.username,
    u.email,
    u.full_name
FROM 
    ims_users u
    JOIN user_modules um ON u.id = um.user_id
WHERE 
    um.module_id = (SELECT id FROM modules WHERE name = 'purchase')
    AND u.is_active = TRUE
ORDER BY 
    u.username;

-- Clear all modules from a user
DELETE FROM user_modules
WHERE user_id = (SELECT id FROM ims_users WHERE username = 'john_doe');


-- =====================================================
-- 4. PERMISSION MANAGEMENT QUERIES
-- =====================================================

-- Set purchase permissions for a user
INSERT INTO purchase_permissions (user_id, can_create, can_edit, can_approve, can_delete, can_view)
VALUES (
    (SELECT id FROM ims_users WHERE username = 'john_doe'),
    TRUE,  -- can_create
    TRUE,  -- can_edit
    FALSE, -- can_approve
    FALSE, -- can_delete
    TRUE   -- can_view
)
ON CONFLICT (user_id) 
DO UPDATE SET
    can_create = EXCLUDED.can_create,
    can_edit = EXCLUDED.can_edit,
    can_approve = EXCLUDED.can_approve,
    can_delete = EXCLUDED.can_delete,
    can_view = EXCLUDED.can_view,
    updated_at = NOW();

-- Set transfer permissions
INSERT INTO transfer_permissions (user_id, can_create, can_edit, can_approve, can_delete, can_view)
VALUES (
    (SELECT id FROM ims_users WHERE username = 'john_doe'),
    TRUE, TRUE, FALSE, FALSE, TRUE
)
ON CONFLICT (user_id) 
DO UPDATE SET
    can_create = EXCLUDED.can_create,
    can_edit = EXCLUDED.can_edit,
    can_approve = EXCLUDED.can_approve,
    can_delete = EXCLUDED.can_delete,
    can_view = EXCLUDED.can_view,
    updated_at = NOW();

-- Set RTV permissions
INSERT INTO rtv_permissions (user_id, can_create, can_edit, can_approve, can_delete, can_view)
VALUES (
    (SELECT id FROM ims_users WHERE username = 'john_doe'),
    TRUE, TRUE, FALSE, FALSE, TRUE
)
ON CONFLICT (user_id) 
DO UPDATE SET
    can_create = EXCLUDED.can_create,
    can_edit = EXCLUDED.can_edit,
    can_approve = EXCLUDED.can_approve,
    can_delete = EXCLUDED.can_delete,
    can_view = EXCLUDED.can_view,
    updated_at = NOW();

-- Set sales permissions
INSERT INTO sales_permissions (user_id, can_create, can_edit, can_approve, can_delete, can_view)
VALUES (
    (SELECT id FROM ims_users WHERE username = 'john_doe'),
    TRUE, TRUE, FALSE, FALSE, TRUE
)
ON CONFLICT (user_id) 
DO UPDATE SET
    can_create = EXCLUDED.can_create,
    can_edit = EXCLUDED.can_edit,
    can_approve = EXCLUDED.can_approve,
    can_delete = EXCLUDED.can_delete,
    can_view = EXCLUDED.can_view,
    updated_at = NOW();

-- Set printing permissions
INSERT INTO printing_permissions (user_id, can_create, can_edit, can_approve, can_delete, can_view)
VALUES (
    (SELECT id FROM ims_users WHERE username = 'john_doe'),
    TRUE, TRUE, FALSE, FALSE, TRUE
)
ON CONFLICT (user_id) 
DO UPDATE SET
    can_create = EXCLUDED.can_create,
    can_edit = EXCLUDED.can_edit,
    can_approve = EXCLUDED.can_approve,
    can_delete = EXCLUDED.can_delete,
    can_view = EXCLUDED.can_view,
    updated_at = NOW();

-- Get all permissions for a user
SELECT 
    'purchase' AS module,
    can_create, can_edit, can_approve, can_delete, can_view
FROM 
    purchase_permissions
WHERE 
    user_id = (SELECT id FROM ims_users WHERE username = 'john_doe')

UNION ALL

SELECT 
    'transfers' AS module,
    can_create, can_edit, can_approve, can_delete, can_view
FROM 
    transfer_permissions
WHERE 
    user_id = (SELECT id FROM ims_users WHERE username = 'john_doe')

UNION ALL

SELECT 
    'rtv' AS module,
    can_create, can_edit, can_approve, can_delete, can_view
FROM 
    rtv_permissions
WHERE 
    user_id = (SELECT id FROM ims_users WHERE username = 'john_doe')

UNION ALL

SELECT 
    'sales' AS module,
    can_create, can_edit, can_approve, can_delete, can_view
FROM 
    sales_permissions
WHERE 
    user_id = (SELECT id FROM ims_users WHERE username = 'john_doe')

UNION ALL

SELECT 
    'printing' AS module,
    can_create, can_edit, can_approve, can_delete, can_view
FROM 
    printing_permissions
WHERE 
    user_id = (SELECT id FROM ims_users WHERE username = 'john_doe');

-- Update specific permission for a user in purchase module
UPDATE purchase_permissions
SET 
    can_approve = TRUE,
    updated_at = NOW()
WHERE 
    user_id = (SELECT id FROM ims_users WHERE username = 'john_doe');

-- Remove all purchase permissions for a user
DELETE FROM purchase_permissions
WHERE user_id = (SELECT id FROM ims_users WHERE username = 'john_doe');


-- =====================================================
-- 5. COMPLEX QUERIES FOR REPORTING
-- =====================================================

-- Get complete user profile with modules and permissions
SELECT 
    u.id,
    u.username,
    u.email,
    u.full_name,
    u.is_active,
    u.is_superuser,
    u.last_login,
    u.created_at,
    
    -- Modules
    (SELECT STRING_AGG(m.name, ', ' ORDER BY m.name)
     FROM user_modules um
     JOIN modules m ON um.module_id = m.id
     WHERE um.user_id = u.id) AS modules,
    
    -- Purchase permissions
    pp.can_create AS purchase_create,
    pp.can_edit AS purchase_edit,
    pp.can_approve AS purchase_approve,
    pp.can_delete AS purchase_delete,
    pp.can_view AS purchase_view,
    
    -- Transfer permissions
    tp.can_create AS transfer_create,
    tp.can_edit AS transfer_edit,
    tp.can_approve AS transfer_approve,
    tp.can_delete AS transfer_delete,
    tp.can_view AS transfer_view,
    
    -- RTV permissions
    rp.can_create AS rtv_create,
    rp.can_edit AS rtv_edit,
    rp.can_approve AS rtv_approve,
    rp.can_delete AS rtv_delete,
    rp.can_view AS rtv_view,
    
    -- Sales permissions
    sp.can_create AS sales_create,
    sp.can_edit AS sales_edit,
    sp.can_approve AS sales_approve,
    sp.can_delete AS sales_delete,
    sp.can_view AS sales_view,
    
    -- Printing permissions
    prp.can_create AS printing_create,
    prp.can_edit AS printing_edit,
    prp.can_approve AS printing_approve,
    prp.can_delete AS printing_delete,
    prp.can_view AS printing_view
    
FROM 
    ims_users u
    LEFT JOIN purchase_permissions pp ON u.id = pp.user_id
    LEFT JOIN transfer_permissions tp ON u.id = tp.user_id
    LEFT JOIN rtv_permissions rp ON u.id = rp.user_id
    LEFT JOIN sales_permissions sp ON u.id = sp.user_id
    LEFT JOIN printing_permissions prp ON u.id = prp.user_id
WHERE 
    u.username = 'john_doe';


-- Get all users with approval permissions in any module
SELECT DISTINCT
    u.id,
    u.username,
    u.email,
    u.full_name,
    CASE 
        WHEN u.is_superuser THEN 'Superuser'
        ELSE 'Regular User'
    END AS user_type
FROM 
    ims_users u
    LEFT JOIN purchase_permissions pp ON u.id = pp.user_id
    LEFT JOIN transfer_permissions tp ON u.id = tp.user_id
    LEFT JOIN rtv_permissions rp ON u.id = rp.user_id
    LEFT JOIN sales_permissions sp ON u.id = sp.user_id
    LEFT JOIN printing_permissions prp ON u.id = prp.user_id
WHERE 
    u.is_active = TRUE
    AND (
        u.is_superuser = TRUE
        OR pp.can_approve = TRUE
        OR tp.can_approve = TRUE
        OR rp.can_approve = TRUE
        OR sp.can_approve = TRUE
        OR prp.can_approve = TRUE
    )
ORDER BY 
    u.username;


-- Count users by module
SELECT 
    m.name AS module_name,
    m.display_name,
    COUNT(um.user_id) AS user_count
FROM 
    modules m
    LEFT JOIN user_modules um ON m.id = um.module_id
    LEFT JOIN ims_users u ON um.user_id = u.id AND u.is_active = TRUE
GROUP BY 
    m.id, m.name, m.display_name
ORDER BY 
    user_count DESC, m.name;


-- Get users without any module assignments
SELECT 
    u.id,
    u.username,
    u.email,
    u.full_name,
    u.is_superuser
FROM 
    ims_users u
    LEFT JOIN user_modules um ON u.id = um.user_id
WHERE 
    u.is_active = TRUE
    AND um.user_id IS NULL
    AND u.is_superuser = FALSE
ORDER BY 
    u.created_at DESC;


-- Get users without any permissions set
SELECT 
    u.id,
    u.username,
    u.email,
    u.full_name
FROM 
    ims_users u
    LEFT JOIN purchase_permissions pp ON u.id = pp.user_id
    LEFT JOIN transfer_permissions tp ON u.id = tp.user_id
    LEFT JOIN rtv_permissions rp ON u.id = rp.user_id
    LEFT JOIN sales_permissions sp ON u.id = sp.user_id
    LEFT JOIN printing_permissions prp ON u.id = prp.user_id
WHERE 
    u.is_active = TRUE
    AND u.is_superuser = FALSE
    AND pp.id IS NULL
    AND tp.id IS NULL
    AND rp.id IS NULL
    AND sp.id IS NULL
    AND prp.id IS NULL
ORDER BY 
    u.username;


-- =====================================================
-- 6. AUDIT AND MONITORING QUERIES
-- =====================================================

-- Get recently created users (last 30 days)
SELECT 
    id,
    username,
    email,
    full_name,
    created_at
FROM 
    ims_users
WHERE 
    created_at >= NOW() - INTERVAL '30 days'
ORDER BY 
    created_at DESC;

-- Get recently logged in users (last 7 days)
SELECT 
    id,
    username,
    email,
    full_name,
    last_login
FROM 
    ims_users
WHERE 
    last_login >= NOW() - INTERVAL '7 days'
    AND is_active = TRUE
ORDER BY 
    last_login DESC;

-- Get inactive users (never logged in or not logged in for 90 days)
SELECT 
    id,
    username,
    email,
    full_name,
    created_at,
    last_login,
    COALESCE(last_login, created_at) AS last_activity
FROM 
    ims_users
WHERE 
    is_active = TRUE
    AND (
        last_login IS NULL
        OR last_login < NOW() - INTERVAL '90 days'
    )
ORDER BY 
    last_activity DESC;

-- Get user activity summary
SELECT 
    COUNT(*) AS total_users,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) AS active_users,
    COUNT(CASE WHEN is_active = FALSE THEN 1 END) AS inactive_users,
    COUNT(CASE WHEN is_superuser = TRUE THEN 1 END) AS superusers,
    COUNT(CASE WHEN last_login IS NOT NULL THEN 1 END) AS users_with_login,
    COUNT(CASE WHEN last_login >= NOW() - INTERVAL '7 days' THEN 1 END) AS active_last_week,
    COUNT(CASE WHEN last_login >= NOW() - INTERVAL '30 days' THEN 1 END) AS active_last_month
FROM 
    ims_users;


-- =====================================================
-- 7. DATA VALIDATION QUERIES
-- =====================================================

-- Check for duplicate emails
SELECT 
    email,
    COUNT(*) AS count
FROM 
    ims_users
WHERE 
    email IS NOT NULL
GROUP BY 
    email
HAVING 
    COUNT(*) > 1;

-- Check for users without email
SELECT 
    id,
    username,
    full_name
FROM 
    ims_users
WHERE 
    email IS NULL OR email = '';

-- Check for orphaned permissions (users that don't exist)
SELECT 'purchase' AS module, COUNT(*) AS orphaned_count
FROM purchase_permissions pp
LEFT JOIN ims_users u ON pp.user_id = u.id
WHERE u.id IS NULL

UNION ALL

SELECT 'transfers', COUNT(*)
FROM transfer_permissions tp
LEFT JOIN ims_users u ON tp.user_id = u.id
WHERE u.id IS NULL

UNION ALL

SELECT 'rtv', COUNT(*)
FROM rtv_permissions rp
LEFT JOIN ims_users u ON rp.user_id = u.id
WHERE u.id IS NULL

UNION ALL

SELECT 'sales', COUNT(*)
FROM sales_permissions sp
LEFT JOIN ims_users u ON sp.user_id = u.id
WHERE u.id IS NULL

UNION ALL

SELECT 'printing', COUNT(*)
FROM printing_permissions prp
LEFT JOIN ims_users u ON prp.user_id = u.id
WHERE u.id IS NULL;
