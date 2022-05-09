# Example script of taking raster tiles in `map.rasters` and converting them to a GeoTIFF
import psycopg2
import rasterio
from rasterio.io import MemoryFile
from pathlib import Path

save_path = Path('data/raster.tif')
conn = psycopg2.connect(
    'host=localhost port=5432 dbname=postgres user=postgres password=postgres')
cur = conn.cursor()

cur.execute("""--sql
    SET postgis.gdal_enabled_drivers = 'ENABLE_ALL';
    SELECT ST_AsGDALRaster(ST_Union(rast), 'GTiff') as tiff
    FROM map.rasters;
""")
result = cur.fetchone()
if result is not None:
    bytes = result[0].tobytes()
    with MemoryFile(bytes) as memfile:
        ds = memfile.open()
        with rasterio.open(save_path, 'w', **ds.profile) as dest:
            dest.write(ds.read())

conn.commit()
cur.close()
conn.close()
