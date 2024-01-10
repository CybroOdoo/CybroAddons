# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (<https://www.cybrosys.com>)
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
import os
from odoo.addons.web.controllers.home import Home
from odoo import http
from odoo.http import request


class ImageController(Home):

    def image_capture(self):
        # Function to take image when user login
        video = cv2.VideoCapture(0)
        while True:
            ret, frames = video.read()
            cv2.imwrite('/tmp/img_name.jpg', frames)
            # The above variable is used to save the image file
            with open("/tmp/img_name.jpg", "rb") as img_file:
                b64_string = base64.b64encode(img_file.read())
                if not request.params['login_success']:
                    request.env['user.log'].sudo().create(
                        {'image': b64_string,
                         'secure': True})
                else:
                    request.env['user.log'].sudo().create(
                        {'user_id': request.env.user.id,
                         'image': b64_string})
                os.remove('/tmp/img_name.jpg')
                video.release()
                cv2.destroyAllWindows()
                break

    @http.route()
    def web_login(self, redirect=None, **kw):
        """Used to log in the user and here is the function for store the
                logged user record"""
        res = super().web_login()
        if (request.httprequest.method == 'POST'
                and request.params['login_success']):
            self.image_capture()
        if (request.httprequest.method == 'POST'
                and not request.params['login_success']):
            self.image_capture()
        return res
