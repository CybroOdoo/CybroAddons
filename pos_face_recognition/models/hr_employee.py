# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import base64
import cv2
import face_recognition
from io import BytesIO
import numpy as np
from PIL import Image
import time
from odoo import api, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    """For comparing image """

    @api.model
    def camera_open(self, kwargs):
        """Capture the image from webcam and compare
        with already  saved image"""
        cap = cv2.VideoCapture(0)  # 0 is the index of the default camera
        image = self.env['hr.employee'].browse(kwargs["id"]).image_1920
        binary_data = base64.b64decode(image)
        image_bytes = BytesIO(binary_data)
        pil_image = Image.open(image_bytes)
        np_image = np.array(pil_image)
        img_saved = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
        encode_image_saved = face_recognition.face_encodings(img_saved)
        face_recognized = 0
        start_time = time.time()
        camera_time = 0
        login_now = 0
        while True:
            ret, frame = cap.read()  # Read a frame from the camera
            cv2.imshow('frame', frame)  # Display the frame
            imgs = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
            imgs = cv2.cvtColor(imgs, cv2.COLOR_BGR2RGB)
            face_current_frame = face_recognition.face_locations(imgs)
            encode_current_frame = face_recognition.face_encodings(
                imgs,
                face_current_frame)
            for encodeFace, faceLoc in zip(encode_current_frame,
                                           face_current_frame):
                matches1 = face_recognition.compare_faces(encode_image_saved,
                                                          encodeFace)
                face_distance = face_recognition.face_distance(
                    encode_image_saved,
                    encodeFace)
                match_index = np.argmin(face_distance)
                elapsed_time = time.time() - start_time
                if matches1[match_index]:
                    face_recognized = 1
                    if elapsed_time > 6:
                        login_now = 1
                        cap.release()
                        break
            if login_now == 1:
                break
            if camera_time < 40 and login_now == 0:
                camera_time = camera_time + 1
            else:
                cap.release()
                cv2.destroyAllWindows()
                break
            if cv2.waitKey(1) == ord('q'):
                break
        cap.release()  # Release the camera
        cv2.destroyAllWindows()  # Close all windows
        return face_recognized
