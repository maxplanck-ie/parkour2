\pset format unaligned
\pset tuples_only on
\pset border 0

WITH table_list AS (
    SELECT DISTINCT table_name 
    FROM information_schema.columns 
    WHERE table_schema = 'public'
    ORDER BY table_name
),
foreign_keys AS (
    SELECT
        kcu.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
)
SELECT format(E'%s:\n%s\n', 
    t.table_name, 
    string_agg(
        format('- %s (%s%s%s%s%s%s)', 
            c.column_name,
            c.udt_name || 
            CASE 
                WHEN c.character_maximum_length IS NOT NULL THEN '(' || c.character_maximum_length || ')'
                ELSE ''
            END,
            CASE WHEN c.is_nullable = 'NO' THEN ', NOT NULL' ELSE '' END,
            CASE WHEN EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage AS ccu 
                ON tc.constraint_name = ccu.constraint_name
                WHERE tc.table_name = c.table_name 
                AND ccu.column_name = c.column_name 
                AND tc.constraint_type = 'PRIMARY KEY'
            ) THEN ', PRIMARY KEY' ELSE '' END,
            CASE WHEN c.column_default IS NOT NULL THEN ', DEFAULT ' || c.column_default ELSE '' END,
            CASE 
                WHEN fk.foreign_table_name IS NOT NULL 
                THEN ', FOREIGN KEY REFERENCES ' || fk.foreign_table_name || '(' || fk.foreign_column_name || ')' 
                ELSE '' 
            END,
            ''
        ),
        E'\n'
        ORDER BY c.ordinal_position
    )
) 
FROM table_list t
JOIN information_schema.columns c ON c.table_name = t.table_name AND c.table_schema = 'public'
LEFT JOIN foreign_keys fk ON fk.table_name = t.table_name AND fk.column_name = c.column_name
GROUP BY t.table_name
ORDER BY t.table_name;