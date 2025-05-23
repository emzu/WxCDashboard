import os
import ee

from google.colab import auth
auth.authenticate_user(project_id="earthengine-23706")

# Trigger the authentication flow.
ee.Authenticate()

# Initialize the library.
ee.Initialize()

import pycrs
import geemap #Python Interface/Extension Library for Earth Engine
import shapely
import zipfile

import geopandas as gpd
import pandas as pd

import fiona
fiona.drvsupport.supported_drivers['libkml'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

def outlineToFields(subak_kmz_filepath):
  #Input: Subak KML filepath
  #Returns: Fields

  # Directory for KML file 
  extraction_dir = os.path.dirname('/content/drive/MyDrive/Research/AWDMonitoring_Bali/Data')

  # Open the KMZ file and extract its contents
  with zipfile.ZipFile(subak_kmz_filepath, "r") as kmz:
      kmz.extractall(extraction_dir)
  #Open the KML and save as a shapefile
  fields_gdf = gpd.read_file('/content/drive/MyDrive/Research/AWDMonitoring_Bali/doc.kml', driver='libkml')
  fields_gdf = fields_gdf[fields_gdf.index % 2 == 1]
  fields_gdf[['Name', 'Status']] = fields_gdf['Name'].str.split('-', expand=True)
  fields_gdf['geometry'] = shapely.wkb.loads(shapely.wkb.dumps(fields_gdf['geometry'], output_dimension=2))
  fields_gdf.to_file("fields2024.shp")

  bbox_bounds = fields_gdf.total_bounds
  bbox = ee.Geometry.Rectangle([bbox_bounds[0], bbox_bounds[1], bbox_bounds[2], bbox_bounds[3]])

  landcover = ee.ImageCollection("ESA/WorldCover/v200").first().clip(bbox)
  #Select only cropland
  cropland = landcover.eq(40)
  cropland = cropland.updateMask(cropland)
  cropland_features = cropland.reduceToVectors(**{
    'geometry': bbox,  # Limit the features to your bounding box
    'scale': 50,       # Adjust scale as needed
    'geometryType': 'polygon',
    'maxPixels': 1e13  # Increase if necessary for large areas
  })

  gridded_cropland = cropland_features.geometry().coveringGrid(cropland.projection())
  return gridded_cropland
