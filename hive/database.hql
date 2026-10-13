-- ==============================================================================
-- Database Provisioning for Music Analytics Warehouse
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS music_warehouse
COMMENT 'Enterprise Data Warehouse for Music Track & Popularity Analytics'
LOCATION '/user/hive/warehouse/music_warehouse.db';

USE music_warehouse;
