# -*- coding: utf-8 -*-
"""
Created on 01/21/2020

@author: broberts

Description: 
	Edit shapefiles for creating the GEE image chunk outputs and for running the clip_and_decompose.py script for the stem framework. 
Input requirements: 
	make_fishnet_grid.py 
	make_processing_tiles.py
	shapefile_path - original input shapefile with your ROI (e.g. CONUS, a state, another country)
	simple_shp_path - in the case that your domain has a bunch of islands or small disconnected areas this will make processing easier. Put None if not used.
	write_to_path - folder where you want your outputs to land
	cell_size - this is the height and width of cells in your vector file for running the clip and decompose step of the STEM framework. Based on CONUS, dividing the width of your domain by ~70 should give you this number
	out_epsg - this is mostly for files that are generated by the make_fishnet_grid.py and may need to be amended but for now give it the final projection you want 
	gee_rows - rows in your GEE vector for generating fitted images
	gee_cols - cols for your GEE vector for generating fitted images

Outputs: 
	'tiles_for_cnd.shp' - vector file for running clip and decompose 
	'ak_gee_tiles_{nrows}_{ncols}_clipped.shp' - vector file for running GEE scripts for generating fitted images

Notes: This is likely to have bugs as it has not been robustly tested with other shapefiles and projections as of 02/12/2020. Updated by Peter 20201802
"""
from lthacks.lthacks import *
import os 
import sys
from osgeo import ogr
import numpy as np 
from subprocess import call
import subprocess
import geopandas as gpd
#from pathlib import Path

#####################################################################################################
#####################################################################################################
#####################################################################################################

def get_shp_extent(input_shape): 
	"""Get shapefile extent and return a tuple."""
	source = ogr.Open(input_shape, update=True)
	#layer = source.GetLayer()
	inLayer = source.GetLayer()
	#create extent tuple 
	extent = inLayer.GetExtent()
	return extent

def reproject(input_shape,epsg): 
	"""Emulate command line ogr reprojection tool."""
	reprojected_filename = input_shape[:-4]+'_reprojected.shp'
	subprocess.call(['ogr2ogr', '-f','ESRI Shapefile', '-t_srs', 'EPSG:{epsg}'.format(epsg=epsg), '-s_srs', 'EPSG:{epsg}'.format(epsg=epsg), reprojected_filename , input_shape])
	return reprojected_filename


def create_cnd_vectors(shp_path,output_filepath,gridsize): 
	"""Takes a boundary shapefile and creates a fishnet version. Requires make_fishnet_grid.py."""
	grid_extent = get_shp_extent(shp_path)
	print(grid_extent)
	#create gee file output name
	output_filename = output_filepath+'cnd_fishnet_{gridsize}_grid.shp'.format(gridsize=int(gridsize))
	try: 
		#check if file has already been created
		if os.path.exists(output_filename):
			print ('cnd file already exists' )
		else:
			print ('making file')
			#call make_fishnet_grid and assign extents from get_shp_extent tuple 
			subprocess.call(['python', 'make_fishnet_grid.py', output_filename, str(grid_extent[0]), str(grid_extent[1]), str(grid_extent[2]), str(grid_extent[3]), str(gridsize), str(gridsize)])
	except RuntimeError:
		print ('That file does not exist' )
		pass
	return output_filename
def make_bounding_fields(input_tiles): 
	"""Add bounding box fields to fishnet file."""
	xmin = []
	xmax = []
	ymin = []
	ymax = []

	source = ogr.Open(input_tiles, update=True)
	layer = source.GetLayer()
	for feature in layer:
		geom = feature.GetGeometryRef()
		extent = geom.GetEnvelope()
		xmin.append(extent[0])
		xmax.append(extent[1])
		ymin.append(extent[2])
		ymax.append(extent[3])
	return xmin,xmax,ymin,ymax

def add_bounding_fields(input_tiles,input_lists): 
	"""Populate new attribute fields."""
	file = gpd.read_file(input_tiles)
	file['xmin'] = input_lists[0]
	file['xmax'] = input_lists[1]
	file['ymin'] = input_lists[2]
	file['ymax'] = input_lists[3]
	file.to_file(input_tiles)
	return input_tiles
		
def intersect_polygons(input_grid,simple_bounds,shp_path,epsg,output_filepath): 
	"""Create file of cnd vector that lines up with ROI bounds."""
	try: 
		grid = gpd.read_file(input_grid)
		#make sure gpd understands the projection
		grid = grid.to_crs('+init=epsg:{epsg}'.format(epsg=epsg))
		#create name and id fields 
		grid.loc[:,('name')] = np.arange(len(grid)).astype(str)
		grid['id'] = grid['name']
		#grid.loc[:,('id')] = np.arange(len(grid)).astype(str)

	except RuntimeError: 
		print ('could not understand grid projection, reprojecting')
		#remove the variable grid if it is stored
		del grid
		#in the case that it cannot find the projection, reproject it [this is a place where people could run into an error]
		reprojected_grid = reproject(input_grid,epsg)
		grid = gpd.read_file(reprojected_grid)
		print ('grid crs is')
		print (grid.crs)
		grid = grid.to_crs('+init=epsg:{epsg}'.format(epsg=epsg))
		
		#create a name field 
		grid.loc[:,('name')] = np.arange(len(grid)).astype(str)
		grid['id'] = grid['name']
		#grid.loc[:,('id')] = np.arange(len(grid)).astype(str)

		print('reprojected file made')
	try: 
		if simple_bounds == None:
			#read in the bounds 
			bounds = gpd.read_file(shp_path)
		else: 
			bounds = gpd.read_file(simple_bounds)
		print ('bounds crs is')
		print (bounds.crs)
		bounds = bounds.to_crs('+init=epsg:{epsg}'.format(epsg=epsg))
		
		print('bounds read in ')

	except RuntimeError: 
		print ('could not understand bounds projection, reprojecting')
		del bounds 
		if simple_bounds == None: 
			reprojected_bounds = reproject(shp_path,epsg)
		else: 
			reprojected_bounds = reproject(simple_bounds,epsg)
		bounds = gpd.read_file(reprojected_bounds)
		bounds = grid.to_crs('+init=epsg:{epsg}'.format(epsg=epsg))

	#join datasets
	spatial_join = gpd.sjoin(grid, bounds, how="inner", op='intersects')
	#spatial_join = spatial_join.to_crs('+init=epsg:{epsg}'.format(epsg=epsg))

	if 'FID' in spatial_join.columns: 
		print ('FID already exists, destroying')
		spatial_join.drop(['FID'],axis=1)
		#create new FID
		spatial_join.loc[:,('FID')]=np.arange(len(spatial_join))
	else: 
		print ('FID does not exist, creating')
		spatial_join.loc[:,('FID')]=np.arange(len(spatial_join))



	#create output name
	sjoin_out_filename = output_filepath+'tiles_for_cnd.shp'


	#write to file
	spatial_join.to_file(sjoin_out_filename)
	#sjoin_out_reprojected = reproject(sjoin_out_filename,epsg)

	return sjoin_out_filename

def create_gee_vectors(input_tiles,output_filepath,nrows,ncols,epsg): 
	"""Build and clip to ROI GEE vector for fitted image outputs."""

	#create gee file output name
	output_filename = output_filepath+'gee_tiles_{nrows}_{ncols}.shp'.format(nrows=nrows,ncols=ncols)
	#create clipped gee file output name
	clipped_filename = output_filepath+'gee_tiles_{nrows}_{ncols}_clipped.shp'.format(nrows=nrows,ncols=ncols)

	try: 
		if os.path.exists(output_filename):
			print ('gee file already exists' )
		else:

			subprocess.call(['python', 'make_processing_tiles.py', '{nrows},{ncols}'.format(nrows=nrows,ncols=ncols), '--tile_path',input_tiles, '--out_path', output_filename])
	except RuntimeError:
		print ('That file does not exist' )
		

	try: 
		if os.path.exists(clipped_filename): 
			print ('clipped gee file already exists')
		else: 
			print('making dissolve file')
			cnd_grid=gpd.read_file(input_tiles)
			dissolve_name = input_tiles[:-4]+'_dissolve.shp'
			cnd_dissolve = cnd_grid.dissolve(by='index_righ')
			cnd_dissolve.to_file(dissolve_name)
			# #create output name
			# #write to file
			print(dissolve_name, clipped_filename, output_filename)
			cmd_clip_vector = 'ogr2ogr -clipsrc '+dissolve_name+' '+clipped_filename+' '+output_filename
			print(cmd_clip_vector)

			#subprocess.call(['ogr2ogr', '-clipsrc', dissolve_name, clipped_filename, output_filename])
			subprocess.call(cmd_clip_vector, shell=True)
	except: 
		pass	


def main(): 



	params = sys.argv[1]
	#print(params)
	with open(str(params)) as f:
		variables = json.load(f)
		
		#construct variables from param file
		unzip_filepath = variables["unzip_filepath"]
		in_filepath = variables["in_filepath"]


	
	shapefile_path = variables['shapefile_path']
	simple_shp_path = variables['simple_shp_path']
	write_to_path = variables['write_to_path']
	cell_size = variables['cell_size']
	out_epsg = variables['out_epsg']
	gee_rows = variables['gee_rows']
	gee_cols = variables['gee_cols']

	# check to see if the file path is real 
	if os.path.exists(shapefile_path):
		print(shapefile_path,' : is real')
	else:
		print('Check the first pathway you entered.')
	# check to see if the file path is real
	if os.path.exists(simple_shp_path):
		print(simple_shp_path,' : is real')
	else:
		print('Check the second pathway you entered.')
	# check to see if the file path is real and if it is not it will make one
	if os.path.exists(write_to_path):
		print(write_to_path,' : is a real location.')
	else:
		print('making directory at : ', write_to_path)
		os.mkdir(write_to_path)


	cnd_file = create_cnd_vectors(shapefile_path,write_to_path,float(cell_size))

	
	updated_cnd_file = add_bounding_fields(cnd_file,make_bounding_fields(cnd_file))

	cnd_output=intersect_polygons(cnd_file,simple_shp_path,shapefile_path,out_epsg,write_to_path)

	#gee_file = create_gee_vectors(cnd_output,write_to_path,gee_rows,gee_cols,out_epsg)
	create_gee_vectors(cnd_output,write_to_path,gee_rows,gee_cols,out_epsg)
        
	createMetadata(sys.argv, write_to_path)	

if __name__ == '__main__':
    main()
