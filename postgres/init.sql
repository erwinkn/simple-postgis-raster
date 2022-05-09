-- Add initialization logic here

-- IMPORTANT: modifications in this file will apply upon a full reset of the database,
-- meaning the `postgres/data` folder *must* be deleted

create schema if not exists map;
create extension if not exists postgis_raster;
set search_path = public, map;