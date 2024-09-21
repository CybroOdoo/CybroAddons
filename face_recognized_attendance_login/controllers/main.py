# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP(<https://www.cybrosys.com>)
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

import PIL
import cmake
import cv2
import dlib
import face_recognition
from io import BytesIO

import numpy
import numpy as np
import os
from PIL import Image
import time
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.hr_attendance.controllers.main import HrAttendance
from odoo import _, http


class HrAttendances(HrAttendance):
    """Controllers Overrides to add the Face detection feature"""

    @http.route('/hr_attendance/attendance_employee_data', type="json",
                auth="public")
    def employee_attendance_data(self, token, employee_id):
        """In this Code section the face detection is added to
        employee_attendance_data"""


        company = self._get_company(token)
        employee_pic = request.env['hr.employee'].sudo().browse(
            employee_id).image_1920
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
        referenced_key_points, referenced_descriptors = orb.detectAndCompute(
            img, None)
        encoded_face = face_recognition.face_encodings(img)
        start_time = time.time()

        camera_time = 0
        face_recognized = 0
        eyes_match_fail_index = 0
        eyes_match_index = 0
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()

        while ret and camera_time < 9:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.bilateralFilter(gray, 5, 1, 1)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5,
                                                  minSize=(200, 200))

            if len(faces) == 1:
                for (x, y, w, h) in faces:
                    frame = cv2.rectangle(frame, (x, y), (x + w, y + h),
                                          (0, 255, 0), 2)
                    eyes = eye_cascade.detectMultiScale(gray, scaleFactor=1.3,
                                                        minNeighbors=5)
                    current_key_points, current_descriptors = orb.detectAndCompute(
                        gray, None)

                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    matches = bf.match(referenced_descriptors,
                                       current_descriptors)
                    good_matches = [m for m in matches if m.distance < 70]

                    if len(good_matches) >= 5:
                        eyes_match_index += 1
                    else:
                        eyes_match_fail_index += 1

                    if len(eyes) == 0:
                        img_frame = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
                        img_frame = cv2.cvtColor(img_frame, cv2.COLOR_BGR2RGB)
                        face_current_frame = face_recognition.face_locations(
                            img_frame)
                        encode_current_frame = face_recognition.face_encodings(
                            img_frame, face_current_frame)

                        for encode_face, face_loc in zip(encode_current_frame,
                                                         face_current_frame):
                            face_matches = face_recognition.compare_faces(
                                encoded_face, encode_face)
                            face_distance = face_recognition.face_distance(
                                encoded_face, encode_face)
                            match_index = np.argmin(face_distance)
                            elapsed_time = time.time() - start_time

                            if face_matches[
                                match_index] and eyes_match_index > eyes_match_fail_index:
                                face_recognized = 1
                                if elapsed_time > 6:
                                    time.sleep(1)
                            else:
                                face_recognized = 0
            # cv2.imshow('frame', frame)
            # the imshow is removed from here because it is not needed anymore
            #  Also it is making error while running the code second time.
                cv2.waitKey(0)
            else:
                # Reset the counters and related variables when no face is
                # detected
                camera_time += 1
                eyes_match_index = 0
                eyes_match_fail_index = 0
        cap.release()
        cv2.destroyAllWindows()
        camera_time = 0
        if company and face_recognized != 1:
            raise AccessError(
                _("Sorry, Can't recognize you. Please try again"))
        else:
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if employee.company_id == company:
                return self._get_employee_info_response(employee)
        cv2.waitKey(0)
        return {}
