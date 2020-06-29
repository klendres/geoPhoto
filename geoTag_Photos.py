#!/usr/bin/python2.4
# -*- coding: cp1252 -*-
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""Reads the EXIF headers from geo-tagged photos. and creates a KML file.

Reads the EXIF headers from geo-tagged photos and creates a KML file with
a PhotoOverlay element for each file. Requires the open source EXIF.py file
downloadable at:

http://sourceforge.net/projects/exif-py/

  GetFile(): Handles the opening of an individual file.
  GetHeaders(): Reads the headers from the file.
  DmsToDecimal(): Converts EXIF GPS headers data to a decimal degree.
  GetGps(): Parses out the the GPS headers from the headers data.
  CreateKmlDoc(): Creates an XML document object to represent the KML document.
  CreatePhotoOverlay: Creates an individual PhotoOverlay XML element object.
  CreateKmlFile(): Creates and writes out a KML document to file.
"""

__author__ = 'mmarks@google.com (Mano Marks)'


import sys
import xml.dom.minidom
#import xml.etree.ElementTree as ET
import time
import glob
import os.path
import imghdr
import zipfile
import exifread
import tkinter as tk
from tkinter import filedialog
from geojson import Point, Feature, FeatureCollection, dump
import json




def splitall(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def GetFile(file_name):
  """Handles opening the file.

  Args:
    file_name: the name of the file to get

  Returns:
    A file
  """

  the_file = None

  try:
    the_file = open(file_name, 'rb')

  except IOError:
    the_file = None

  return the_file





def DmsToDecimal(degree_num, degree_den, minute_num, minute_den,
                 second_num, second_den):
  """Converts the Degree/Minute/Second formatted GPS data to decimal degrees.

  Args:
    degree_num: The numerator of the degree object.
    degree_den: The denominator of the degree object.
    minute_num: The numerator of the minute object.
    minute_den: The denominator of the minute object.
    second_num: The numerator of the second object.
    second_den: The denominator of the second object.

  Returns:
    A deciminal degree.
  """

  degree = float(degree_num)/float(degree_den)
  minute = float(minute_num)/float(minute_den)/60
  second = float(second_num)/float(second_den)/3600
  return degree + minute + second


def GetGps(data):
  """Parses out the GPS coordinates from the file.

  Args:
    data: A dict object representing the EXIF headers of the photo.

  Returns:
    A tuple representing the latitude, longitude, and altitude of the photo.
  """
  try:
    lat_dms = data['GPS GPSLatitude'].values
    long_dms = data['GPS GPSLongitude'].values
  except:
    print ("    No GPS Coordinates for Photo")
    return [0,0,0]


  if str(lat_dms[0]) == '0/0':
    print ("    No GPS Coordinates for Photo")
    return [0,0,0]
  latitude = DmsToDecimal(lat_dms[0].num, lat_dms[0].den,
                          lat_dms[1].num, lat_dms[1].den,
                          lat_dms[2].num, lat_dms[2].den)
  longitude = DmsToDecimal(long_dms[0].num, long_dms[0].den,
                           long_dms[1].num, long_dms[1].den,
                           long_dms[2].num, long_dms[2].den)
  if data['GPS GPSLatitudeRef'].printable == 'S': latitude *= -1
  if data['GPS GPSLongitudeRef'].printable == 'W': longitude *= -1
  altitude = None

  try:
    alt = data['GPS GPSAltitude'].values[0]
    altitude = alt.num/alt.den
    if data['GPS GPSAltitudeRef'] == 1: altitude *= -1

  except KeyError:
    altitude = 0

  return latitude, longitude, altitude


def CreateKmlDoc(title):
  """Creates a KML document."""

  kml_doc = xml.dom.minidom.Document()
  kml_element = kml_doc.createElementNS('http://www.opengis.net/kml/2.2', 'kml')
  kml_element.setAttribute('xmlns', 'http://www.opengis.net/kml/2.2')
  kml_element = kml_doc.appendChild(kml_element)
  document = kml_doc.createElement('Document')
  kml_element.appendChild(document)
  name = kml_doc.createElement('name')
  name.appendChild(kml_doc.createTextNode(title))
  document.appendChild(name)
  openstatus = kml_doc.createElement('open')
  openstatus.appendChild(kml_doc.createTextNode('1'))
  document.appendChild(openstatus)
  style = kml_doc.createElement('Style')
  style.setAttribute('id','Photo')
  document.appendChild(style)
  istyle = kml_doc.createElement('IconStyle')
  style.appendChild(istyle)
  scale = kml_doc.createElement('scale')
  scale.appendChild(kml_doc.createTextNode('1.0'))
  istyle.appendChild(scale)
  icon = kml_doc.createElement('Icon')
  href = kml_doc.createElement('href')
  href.appendChild(kml_doc.createTextNode('http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'))
  icon.appendChild(href)
  istyle.appendChild(icon)
  folder = kml_doc.createElement('Folder')
  fname =kml_doc.createElement('name')
  fname.appendChild(kml_doc.createTextNode('GPS Tagged Photos'))
  folder.appendChild(fname)
  document.appendChild(folder)
  folder = kml_doc.createElement('Folder')
  fname =kml_doc.createElement('name')
  fname.appendChild(kml_doc.createTextNode('Photos Without GPS Tag'))
  folder.appendChild(fname)
  document.appendChild(folder)

  return kml_doc


def CreatePhotoOverlay(kml_doc, file_name, the_file, file_iterator):
  """Creates a PhotoOverlay element in the kml_doc element.

  Args:
    kml_doc: An XML document object.
    file_name: The name of the file.
    the_file: The file object.
    file_iterator: The file iterator, used to create the id.

  Returns:
    An XML element representing the PhotoOverlay.
  """

  photo_id = 'photo%s' % file_iterator

  folderId = '-'.join(splitall(file_name)[:-1])
  print(folderId)



  tags = exifread.process_file(the_file,details=False)
#   for tag in tags.keys():
#     if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
#         print "Key: %s, value %s" % (tag, tags[tag])


  try:
      timestamp = tags.get('EXIF DateTimeOriginal').__str__()
  except:
      timestamp = 'No timestamp'
  coords = GetGps(tags)

  GeoPoint = Point((coords[1],coords[0]))
  orientation = tags.get('Image Orientation').__str__()
  if orientation:
    print (orientation)
  else:
    print("No Orientation")
  style = ""

  if "180" in orientation:
      print('new style')
      style = "style='-webkit-transform: rotate(-180deg);'"
  if "Rotated 90 CCW"  in orientation:
      print('new style 90 ccw')
      style = "style='-webkit-transform: rotate(90deg);'"

  if coords[0] == 0:
    return

  path,filename = os.path.split(file_name)
  po = kml_doc.createElement('Placemark')
  name = kml_doc.createElement('name')
  name.appendChild(kml_doc.createTextNode(filename))
  description = kml_doc.createElement('description')
  base = os.path.splitext(file_name)[0]
  ext = os.path.splitext(file_name)[1]
  file_name = base + ext.lower()
  cdata = "<h2>Date: "+timestamp+"</h2><h3>Latitude: "+str(coords[0])+"</h3><h3>Longitude: "+str(coords[1])+"</h3><img src='./"+file_name+"' width=600 "+style+" >"

  description.appendChild(kml_doc.createCDATASection(cdata))
  po.appendChild(name)
  po.appendChild(description)
  styleurl = kml_doc.createElement('styleUrl')
  styleurl.appendChild(kml_doc.createTextNode('#Photo'))
  po.appendChild(styleurl)

  point = kml_doc.createElement('Point')
  amode = kml_doc.createElement('altitudeMode')
  amode.appendChild(kml_doc.createTextNode('clampToGround'))
  point.appendChild(amode)

  coordtext = kml_doc.createElement('coordinates')


  value = str(coords[1])+","+str(coords[0])+","+str(coords[2])

  coordtext.appendChild(kml_doc.createTextNode(value))
  point.appendChild(coordtext)
  po.appendChild(point)

  folder = kml_doc.getElementsByTagName('Folder')[0]
  for node in kml_doc.getElementsByTagName('Folder'):  # visit every node <bar />
    if node.getElementsByTagName("id"):
      name = node.getElementsByTagName("id")[0]
      if folderId == name.firstChild.data:
        folder = node
  folder.appendChild(po)
  if "EXIF DateTimeOriginal" in tags:
      DateTime = tags.get('EXIF DateTimeOriginal').__str__()
  else:
      DateTime = 0

  if "GPS GPSDate" in tags:
      GPSTime = tags.get('GPS GPSDate').__str__()
  else:
      GPSTime = 0

  return Feature(geometry=GeoPoint, properties={
      "Datetime": DateTime,
      "GPSDate" : GPSTime,
      "Path"    : "./"+file_name})



def CreateKmlFile(file_names, new_file_name,title):
  """Creates the KML Document with the PhotoOverlays, and writes it to a file.
  Args:
    file_names: A list object of all the names of the files.
    new_file_name: A string of the name of the new file to be created.
  """
  features = []

  files = {}

  kml_doc = CreateKmlDoc(title)

  for file_name in file_names:
    the_file = GetFile(file_name)
    if the_file is None:
      print ("'%s' is unreadable\n" % file_name)
      file_names.remove(file_name)
      continue
    else:
      files[file_name] = the_file
      photoPath = splitall(file_name)
      level = 0
      folder = kml_doc.getElementsByTagName('Folder')[0]

      #remove the file name and set up folders in kml
      photoPath = photoPath[:-1]
      for part in photoPath:
        create = 1
        for node in folder.getElementsByTagName('Folder'):  # visit every node <bar />
            name = node.getElementsByTagName("name")[0]
            if part == name.firstChild.data:
                #print('This folder Exists')
                folder = node
                create = 0
        if(create):
          print('Creating Folder:'+part)
          nextfolder = kml_doc.createElement('Folder')
          fname =kml_doc.createElement('name')
          folderid = kml_doc.createElement('id')
          folderid.appendChild(kml_doc.createTextNode('-'.join(photoPath)))
          fname.appendChild(kml_doc.createTextNode(part))
          nextfolder.appendChild(folderid)
          nextfolder.appendChild(fname)
          folder.appendChild(nextfolder)
          folder = nextfolder

      #for part in photoPath:



  file_iterator = 0
  for key in files.keys():
  #for key in files.iterkeys():
    print('Working on File: ' + str(key) )
    GeoFeature = CreatePhotoOverlay(kml_doc, key, files[key], file_iterator)
    features.append(GeoFeature)
    file_iterator += 1

  kml_file = open(new_file_name, 'w')
  kml_file.write(kml_doc.toprettyxml())
  feature_collection = FeatureCollection(features)
  with open('Photos.json', 'w') as f:
    dump(feature_collection, f)
  return json.dumps(feature_collection)



def main():
# This function was taken from EXIF.py to directly handle
# command line arguments.

  root = tk.Tk()
  T = tk.Text(root, height=4, width=80)
  T.pack()
  T.insert(tk.END, "Instructions:\n\nSelect the top directory of photos to encode in a KMZ file.\nAll photos below this directory will be included.")
  v = tk.IntVar()

#   tk.Label(root,
#         text="""Choose a programming language:""",
#         justify = tk.LEFT,
#         padx = 20).pack()
#   tk.Radiobutton(root,
#               text="Python",
#               padx = 20,
#               variable=v,
#               value=1).pack(anchor=tk.W)
#   tk.Radiobutton(root,
#               text="Perl",
#               padx = 20,
#               variable=v,
#               value=2).pack(anchor=tk.W)
#   root.mainloop()


  value = tk.filedialog.askdirectory(initialdir = os.getcwd(),title="Select top directory with pictures")
  #value = input("Please enter path to top photo directory [enter for current directory]:")
  if len(value) < 1:
    value =os.getcwd()
  #print(f'You entered {value}')

  filelist = []
  outFileName = os.path.split(value)[1]
  for subdir, dirs, files in os.walk(value):
    for file in files:
        if(imghdr.what(os.path.relpath(subdir+'/'+file)) == 'jpeg'):
            filelist.append(os.path.relpath(subdir+'/'+file))


  args = sys.argv[1:]
  if len(filelist) < 1:
    print ("No 'jpg' or 'jpeg' files found in directory")

  else:
    timestr = time.strftime(outFileName+" - Processed %Y_%m_%d.kmz")
    zf = zipfile.ZipFile(timestr, mode='w')
    for file in filelist:
      zf.write(file)
    title = os.path.split(os.getcwd())[1]
    geoJsonCollection = CreateKmlFile(filelist, 'doc.kml',title)
  zf.write('doc.kml')
  zf.close()

  #remove the temporary doc.kml file
  #if os.path.exists("doc.kml"):
  #  os.remove("doc.kml")

  #input file
  fin = open("LeafletMap_template.html", "rt")
  #output file to write the result to
  fout = open("Working_LeafletMap.html", "wt")
  #for each line in the input file
  for line in fin:
    #read replace the string and write to output file
    fout.write(line.replace('<GEOJSON_PHOTOS>', geoJsonCollection))
  #close input and output files
  fin.close()
  fout.close()

if __name__ == '__main__':
  main()
