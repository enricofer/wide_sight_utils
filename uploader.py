# -*- coding: utf-8 -*-


import os
import requests

IMAGES_FOLDER='/home/urb/pub/20181023'
SEQUENCE = 'ad5713f1-b770-45cc-9998-38a20bc873d8'
APIKEY = '375368dfd01b9bd9d26e2284ce18398adbd07e93'
BACKEND = 'http://localhost:8989/panoramas/?apikey='+APIKEY




for image_file in os.listdir(IMAGES_FOLDER):
    f, file_extension = os.path.splitext(image_file)
    if file_extension.upper() in ('.JPG','.JPEG'):
        image_path = os.path.join(IMAGES_FOLDER,image_file)
        image = open(image_path, 'rb')

        multipart_form_data = {
            'eqimage': (image_file, image),
            'sequence': ('', SEQUENCE),
        }

        response = requests.post(BACKEND, files=multipart_form_data)

        print (f, response.json())
        if response.status_code != 201: #http 201: created
            break
