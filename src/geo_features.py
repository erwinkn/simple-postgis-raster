import psycopg2

conn = psycopg2.connect('host=localhost port=5432 dbname=postgres user=postgres password=postgres')

cur = conn.cursor()
cur.execute("""--sql
    drop table if exists map.deposits cascade;

    create table map.deposits (
        id serial primary key,
        description text,
        geometry geometry(Point,2154) not null
    );

    insert into map.deposits (description, geometry)
    select descr, ST_CENTROID(geo.geometry)
    from map.s_fgeol geo
    where descr ilike '%silicates calciques%';

    create index idx_map_deposits_geom
    on map.deposits
    using GIST (geometry);
""")
conn.commit()
cur.close()
conn.close()

# VACUUM ANALYZE is recommended after creating a spatial index, to ensure it can be properly used by Postgres
# However, the command cannot be executed in a transaction, while pscyopg2 automatically starts transactions.
# For this reason, we have to close and start a new connection + enable auto-commit to execute statements outside a transaction.
conn = psycopg2.connect('host=localhost port=5432 dbname=postgres user=postgres password=postgres')
conn.autocommit = True
cursor = conn.cursor()
cursor.execute("VACUUM ANALYZE map.deposits")