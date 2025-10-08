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
# import base64
# import cv2
# import face_recognition
# import numpy as np
# import os
# import time
# from io import BytesIO
# from PIL import Image
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

        return employee_pic

    @api.model
    def get_kiosk_image(self, id):
        """This function is used for attendance  Check In and Check Out in kiosk mode.
        It works by compare the image of employee that already uploaded
        to the image that get currently from the webcam. This function
        also detect the blinking of eyes and calculate the eye match index,
        to ensure that it's a human, not an image of employee"""
        employee_pic = self.browse(id).image_1920
        return employee_pic
