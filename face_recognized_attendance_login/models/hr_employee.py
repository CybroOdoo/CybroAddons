# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import cv2
import face_recognition
import numpy as np
import os
import time
from io import BytesIO
from PIL import Image
from odoo import api, models


class HrEmployee(models.Model):
    """This class inherits the model 'hr.employee' to fetch the image of the
    employee, and later it will compare with the fetched image from camera """
    _inherit = 'hr.employee'

    @api.model
    def get_login_screen(self):
        """This function is used for attendance Check In and Check Out .
        It works by compare the image of employee that already uploaded
        to the image that get currently from the webcam. This function
        also detect the blinking of eyes and calculate the eye match index,
        to ensure that it's a human, not an image of employee"""
        employee_pic = self.search(
            [('user_id', '=', self.env.user.id)]).image_1920
        sub_folder = os.path.abspath(os.path.dirname(__file__))
        project_folder = os.path.abspath(os.path.join(sub_folder, os.pardir))
        eye_cascade_path = os.path.join(project_folder, 'data',
                                        'haarcascade_eye_tree_eyeglasses.xml')
        face_cascade_path = os.path.join(project_folder, 'data',
                                         'haarcascade_frontalface_default.xml')
        face_cascade = cv2.CascadeClassifier(face_cascade_path)
        eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
        binary_data = base64.b64decode(employee_pic)
        image_bytes = BytesIO(binary_data)
        pil_image = Image.open(image_bytes)
        np_image = np.array(pil_image)
        img = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
        # Extract features from the referenced eye(s)
        orb = cv2.ORB_create()
        referenced_key_points, referenced_descriptors = orb.detectAndCompute(img, None)
        encoded_face = face_recognition.face_encodings(img)
        start_time = time.time()
        camera_time = 0
        face_recognized = 0
        eyes_match_fail_index = 0
        eyes_match_index = 0
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        while ret:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.bilateralFilter(gray, 5, 1, 1)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5,
                                                  minSize=(200, 200))
            if camera_time < 100:
                camera_time = camera_time + 1
            else:
                break
            cv2.putText(frame, "Please wait... your face is detecting",
                        (100, 100),
                        cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 2)
            if len(faces) == 1:
                for (x, y, w, h) in faces:
                    frame = cv2.rectangle(frame, (x, y), (x + w, y + h),
                                          (0, 255, 0), 2)
                    eyes = eye_cascade.detectMultiScale(gray, scaleFactor=1.3,
                                                        minNeighbors=5)
                    # Extract features from the eye(s) in the current frame
                    current_key_points, current_descriptors = orb.detectAndCompute(gray, None)
                    # Match the features of the current eye(s) to those in
                    # the reference eye(s)
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    matches = bf.match(referenced_descriptors, current_descriptors)
                    good_matches = [m for m in matches if m.distance < 50]
                    if len(good_matches) >= 10:
                        eyes_match_index = eyes_match_index + 1
                    else:
                        eyes_match_fail_index = eyes_match_fail_index + 1
                    if len(eyes) == 0:
                        img_frame = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
                        img_frame = cv2.cvtColor(img_frame, cv2.COLOR_BGR2RGB)
                        face_current_frame = face_recognition.face_locations(
                            img_frame)
                        encode_current_frame = face_recognition.face_encodings(
                            img_frame,
                            face_current_frame)
                        for encode_face, face_loc in zip(encode_current_frame,
                                                         face_current_frame):
                            face_matches = face_recognition.compare_faces(
                                encoded_face, encode_face)
                            face_distance = face_recognition.face_distance(
                                encoded_face, encode_face)
                            match_index = np.argmin(face_distance)
                            elapsed_time = time.time() - start_time
                            if face_matches[match_index] and eyes_match_index > eyes_match_fail_index:
                                face_recognized = 1
                                if elapsed_time > 6:
                                    time.sleep(1)
                if camera_time >= 100:
                    break
            cv2.imshow('frame', frame)
            cv2.waitKey(1)
        cap.release()
        cv2.destroyAllWindows()
        return face_recognized
