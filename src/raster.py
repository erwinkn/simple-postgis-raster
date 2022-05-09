import psycopg2

conn = psycopg2.connect(
    'host=localhost port=5432 dbname=postgres user=postgres password=postgres')
cur = conn.cursor()

# CAREFUL: we are setting a high value for work_mem to make our heavy query slightly faster
# Do NOT do this in a production setting, where there may be many concurrent queries
# (each can take up to `work_mem`` RAM)
cur.execute('set work_mem to "3GB";')
cur.execute("""--sql
create or replace function map.france_tiles() returns raster as $$
declare
    contour geometry;
    rast raster;
    xmin double precision;
    ymax double precision;
begin
    select ST_Union (geometry) 
    into contour
    from map.departments;

    select ST_XMin(contour) into xmin;
    select ST_YMax(contour) into ymax;

    select ST_AsRaster(
        contour,
        -- A cast to double precision is necessary to ensure the right function overload is picked
        500::double precision, 500::double precision, -- scaleX, scaleY = size of each pixel
        '32BUI'::text, -- each pixel contains a uint32
        0, -- default value
        2147483647, -- no data value (max Postgres integer value)
        xmin, ymax, -- coordinates of the upper left corner of the grid
        0, 0, -- skewx, skewy
        false -- don't keep the pixels that touch a border of the contour
    ) into rast;
    return rast;
end;
$$ language plpgsql volatile;

create or replace function map.cost_raster_fn(rasters double precision[][][], positions integer[][], VARIADIC userargs text[])
returns integer
as $$
declare
    x integer;
    y integer;
    minx double precision;
    maxy double precision;
    scalex double precision;
    scaley double precision;
    srid integer;
    location geometry(point);
    worldx bigint;
    worldy bigint;
    department bigint;
    elec double precision;
    mats double precision;
    transport double precision;
    dist_to_deposit float;
begin
    -- Strategy:
    -- 1. Determine department
    -- 2. Get elec price, transport price, material price
    -- 3. Determine distance to closest deposit
    -- 4. Compute final value

    if rasters[1][1][1] is null then
        -- no data
        return null;
    end if; 

    x := positions[0][1] - 1;
    y := positions[0][2] - 1;
    minx := userargs[3];
    maxy := userargs[4];
    scalex := userargs[5];
    scaley := userargs[6];
    srid := userargs[9];
    location := ST_SetSRID(
        ST_MakePoint(
            minx + x * scalex,
            maxy + y * scaley
        ),
        srid
    );

    select d.code, elec_price, mats_price, transport_price
    into department, elec, mats, transport
    from map.departments d
    where ST_Contains(d.geometry, location);

    -- the `<->` distance operator can use the spatial index (ST_Distance does not)
    select min(location <-> d.geometry)
    into dist_to_deposit
    from map.deposits d;

    return transport * dist_to_deposit / 1000 + mats + elec;
end;
$$ language plpgsql stable;



drop table if exists map.rasters cascade;

create table map.rasters (
    id serial primary key,
    rast raster
);

-- Create raster grid covering the polygon of France
-- and apply our model to each cell
insert into map.rasters(rast)
select
    ST_Tile(
        ST_MapAlgebra(
            rast, -- original raster
            1, -- nb of bands
            'map.cost_raster_fn(double precision[], integer[], text[])'::regprocedure,
            '32BUI'::text, -- pixel type
            NULL, -- extent type
            NULL, -- customextend
            NULL, -- distancex
            NULL, -- distancey
            ST_Width(rast)::text,
            ST_Height(rast)::text,
            ST_UpperLeftX(rast)::text,
            ST_UpperLeftY(rast)::text,
            ST_ScaleX(rast)::text,
            ST_ScaleY(rast)::text,
            ST_SkewX(rast)::text,
            ST_SkewY(rast)::text,
            ST_SRID(rast)::text
        ),
        100, 100
    )
from map.france_tiles() rast;

-- Enables AddRasterConstraints to find the map.rasters table
set search_path = map, public;
select AddRasterConstraints('rasters', 'rast');
""")

conn.commit()
cur.close()
conn.close()