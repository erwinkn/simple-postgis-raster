# The simplest possible spatial techno-economic model
A simple demo that builds a large raster tiling from a spatial model. It was built to demonstrates PostGIS capabilities of handling vector and raster data.

The pipeline is the following:
- Download the full geological map of France by department (1:50000 scale, 5.6GB, 512 Shapefiles)
- Find all the calcium silicate deposits in France and store them in a separate table. Their polygon is simplified to its centroid.
- Download a map of France by postal code and aggregate it by department.
- Generate random data by department.
- Generate an empty raster tiling across France, with a resolution of 500x500m.
- Use the department and deposit data to compute a value for each raster tile, based on the distance to the closest deposit and the local department data.

## Setup
[Conda](https://docs.conda.io/en/latest/) is required as a Python package manager, to avoid issues with binary wheels in geospatial packages like `geopandas` or `rasterio`. It's also recommended to setup conda-forge as follows:

```bash
conda config --add channels conda-forge
conda config --set channel_priority strict
```

After that, you should be able to create your Conda environment using:
```
conda env create -f environment.yml
```

Once the environment is created, you should start the PostgreSQL database using:
```
docker compose up -d
```

**Warning:** the settings for Postgres assume up to 5GB of free RAM. If you have less, please adjust `work_mem` and `shared_buffers` in `postgres/postgresql.conf` and the `src/raster.py` script.

Generally, the queries take much less than that, but a higher limit was set for performance reasons. The settings are not meant for production use.

## Running scripts
The scripts and notebooks are meant to be run in a specific order. They can all be found in the `src/` folder
- `geo_map.ipynb` and `departments.ipynb` will download the necessary spatial data (& generate the rest of the data, randomised by department)
- `geo_features.py` extracts calcium silicates deposits from the national geological map and only keeps the centroid of their polygons
- `raster.py` generates the raster tiles
- `raster_to_geotiff.py` produces a GeoTIFF from the generated raster ties
- `bonus/transport_analysis.ipynb` is a complementary notebook, that showcases inconsistencies in the transport cost data that was used in the first version of this demo

## QGIS map
The `map.qgz` file contains a QGIS project that expects a Postgres database running on `localhost:5432` with username and password equal to `postgres`. The vector layer should be in the `map.deposits` table and the raster layer in `map.rasters`.