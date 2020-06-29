title Geotag Photos
IF EXIST "C:\Python26\ArcGIS10.0\python.exe" GOTO ONE
IF EXIST "C:\Python26\ArcGIS10.1\python.exe" GOTO TWO
IF EXIST "C:\Python27\ArcGIS10.1\python.exe" GOTO THREE
IF EXIST "C:\Python27\ArcGIS10.2\python.exe" GOTO FOUR
IF EXIST "C:\Python27\ArcGIS10.5\python.exe" GOTO FIVE
ECHO PYTHON DIRECTORY NOT FOUND ON YOUR SYSTEM
GOTO END

:ONE
C:\Python26\ArcGIS10.0\python.exe  geoTag_Photos.py > "Geotag_photos_LOG.txt"
GOTO END

:TWO
C:\Python26\ArcGIS10.1\python.exe  geoTag_Photos.py > "Geotag_photos_LOG.txt"
GOTO END

:THREE
C:\Python27\ArcGIS10.1\python.exe  geoTag_Photos.py > "Geotag_photos_LOG.txt"
GOTO END

:FOUR
C:\Python27\ArcGIS10.2\python.exe  geoTag_Photos.py > "Geotag_photos_LOG.txt"
GOTO END

:FIVE
C:\Python27\ArcGIS10.5\python.exe  geoTag_Photos.py > "Geotag_photos_LOG.txt" >CON
GOTO END

:END
ECHO Geotag_Photos process complete, log file:Geotag_photos.log
pause
