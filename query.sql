-- select * from bds_data

create table bds_data (
    [id] int NOT NULL IDENTITY(1,1) PRIMARY KEY,
    [pr_id] int,
    [post_url] varchar(2083),
    [value_hash] varchar(100),
    [price] bigint,
    [price_level] int,
    [area] float,
    [area_level] int,
    [rooms] int,
    [toilets] int,
    [direction] int,
    [type] int, 
    [category] int,
    [city] varchar(100),
    [district] int,
    [ward] int,
    [street] int,
    [project] int,
    [trigger_time] DATETIME,    
    [is_valid] bit,
    [valid_from] DATETIME,
    [valid_to] DATETIME,
    [version_number] int
)

-- select * from INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE

-- alter table bds_data
--     drop CONSTRAINT PK__bds_data__3213E83F3A4D11C2

-- drop table bds_data