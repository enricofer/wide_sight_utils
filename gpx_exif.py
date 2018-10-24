# -*- coding: utf-8 -*-

import gpxpy
import exifread
import piexif
import math
import os
from datetime import datetime
from PIL import Image
from fractions import Fraction
import csv

TELEMETRY_FILE="/home/urb/Dropbox/images/20181023080518-e.csv"
GPX_FILE="/home/urb/pub/20181023/mura.gpx"
IMAGES_FOLDER='/home/urb/pub/20181023'


def calculate_initial_compass_bearing(pointA, pointB):
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def set_gps_tags(img_file,mods):

    def to_deg(value, loc):
        """convert decimal coordinates into degrees, munutes and seconds tuple

        Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
        return: tuple like (25, 13, 48.343 ,'N')
        """
        if value < 0:
            loc_value = loc[0]
        elif value > 0:
            loc_value = loc[1]
        else:
            loc_value = ""
        abs_value = abs(value)
        deg =  int(abs_value)
        t1 = (abs_value-deg)*60
        min = int(t1)
        sec = round((t1 - min)* 60, 5)
        return (deg, min, sec, loc_value)


    def change_to_rational(number):
        """convert a number to rantional

        Keyword arguments: number
        return: tuple like (1, 2), (numerator, denominator)
        """
        f = Fraction(str(number))
        return (f.numerator, f.denominator)




    #print (img_file, mods)
    img = Image.open(img_file)
    exif_dict = piexif.load(img.info['exif'])
    #print (exif_dict['GPS'])

    lat_deg = to_deg( mods["lat"], ["S", "N"])
    lng_deg = to_deg( mods["lon"], ["W", "E"])

    exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
    exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

    exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = lat_deg[3]
    exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = exiv_lat
    exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = lng_deg[3]
    exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = exiv_lng
    exif_dict['GPS'][piexif.GPSIFD.GPSAltitudeRef] = 1
    exif_dict['GPS'][piexif.GPSIFD.GPSAltitude] = change_to_rational(round(mods["elevation"],2))
    exif_dict['GPS'][piexif.GPSIFD.GPSImgDirection] = change_to_rational(round(mods["heading"],1))
    if mods["roll"]:
        exif_dict['GPS'][piexif.GPSIFD.GPSRoll] = (int(mods["roll"]),1,)
    if mods["pitch"]:
        exif_dict['GPS'][piexif.GPSIFD.GPSPitch] = (int(mods["pitch"]),1,) #change_to_rational(round(mods["pitch"],3))

    #print (exif_dict['GPS'])
    exif_bytes = piexif.dump(exif_dict)
    img.save(img_file, "jpeg", exif=exif_bytes)

class telemetry_seq:
    points = []
    measures = []

    def appendPoint(self,point):
        self.points.append(point)

    def appendMeasure(self,point):
        self.measures.append(point)

    def interpolate_point(self,time_sample):
        found = None
        for i, point in enumerate(self.points):
            if point.time > time_sample:
                found = True
                break
        if found:
            segment_delta = self.points[i].time - self.points[i-1].time
            interpolation_delta = time_sample - self.points[i-1].time
            interpolation_factor = interpolation_delta.total_seconds() / segment_delta.total_seconds()
            delta_lat = self.points[i].latitude - self.points[i-1].latitude
            delta_lon = self.points[i].longitude - self.points[i-1].longitude
            delta_alt = self.points[i].elevation - self.points[i-1].elevation
            new_lat = self.points[i-1].latitude + delta_lat * interpolation_factor
            new_lon = self.points[i-1].longitude + delta_lon * interpolation_factor
            new_alt = self.points[i-1].elevation + delta_lon * interpolation_factor
            unix_delta = time_sample - datetime.utcfromtimestamp(0)
            roll_pitch = self.interpolate_measure(unix_delta.total_seconds())
            #print(roll_pitch)
            heading = calculate_initial_compass_bearing((self.points[i-1].latitude,self.points[i-1].longitude),(self.points[i].latitude,self.points[i].longitude),)
            return {
                "lat": new_lat,
                "lon": new_lon,
                "heading": heading,
                "elevation": new_alt,
                "roll": roll_pitch[0],
                "pitch": roll_pitch[1],
            }

    def interpolate_measure(self,timestamp_sample):
        if self.measures:
            found = None
            for i,measure in enumerate(self.measures):
                if measure[0] > timestamp_sample:
                    found = True
                    break
            if found:
                res = []
                measure_delta = self.measures[i][0] - self.measures[i-1][0]
                interpolation_delta = timestamp_sample - self.measures[i-1][0]
                interpolation_factor = interpolation_delta / measure_delta
                for k,dim in enumerate(measure[1:]):
                    res.append(self.measures[i-1][k+1] + dim * interpolation_factor)
                return res
        else:
            return [None,None]

start_point = None
#seq_points = points_seq()
seq_telemetry = telemetry_seq()

if TELEMETRY_FILE:
    with open(TELEMETRY_FILE,'r') as csvfile:
        t_reader = csv.reader(csvfile, delimiter=',')
        header = row1 = next(t_reader)
        for row in t_reader:
            seq_telemetry.appendMeasure([int(row[0]), float(row[1]), float(row[2])])

with open(GPX_FILE, 'r') as f:
    gpx = gpxpy.parse(f)

for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            if not start_point:
                start_point = point
                start_time = int(point.time.strftime("%f"))
            seq_telemetry.appendPoint(point)
            #print (point)

print (dir(point))

for image_file in os.listdir(IMAGES_FOLDER):
    f, file_extension = os.path.splitext(image_file)
    if file_extension.upper() in ('.JPG','.JPEG'):
        image_path = os.path.join(IMAGES_FOLDER,image_file)
        image = open(image_path, 'rb')
        tags = exifread.process_file(image)
        image.close()
        image_shottime = datetime.strptime(str(tags['EXIF DateTimeOriginal'])+','+str(tags['EXIF SubSecTimeOriginal']), '%Y:%m:%d  %H:%M:%S,%f')
        set_gps_tags(image_path, seq_telemetry.interpolate_point(image_shottime))
        print (str(tags['EXIF DateTimeOriginal'])+','+str(tags['EXIF SubSecTimeOriginal']))
        #print (image_file, image_shottime, str(tags['EXIF DateTimeOriginal'])+','+str(tags['EXIF SubSecTimeOriginal']))