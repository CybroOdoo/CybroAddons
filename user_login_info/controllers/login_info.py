# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import os
from odoo.addons.web.controllers.home import Home
from odoo import http
from odoo.http import request


import logging
import threading
_logger = logging.getLogger(__name__)

class ImageController(Home):

    def _capture_thread(self, env_user_id, login_success, db_name):
        # Function to take image when user login in a separate thread
        _logger.info("Background thread started for image capture")
        
        try:
            import cv2
        except ImportError:
            _logger.error("OpenCV (cv2) not found in background thread")
            return

        # Explicit imports for Odoo 19 internal components
        from odoo.orm.registry import Registry
        from odoo.api import Environment
        from odoo.orm.utils import SUPERUSER_ID
            
        video = cv2.VideoCapture(0)
        try:
            if not video.isOpened():
                _logger.warning("Camera could not be opened in background thread")
                return
            ret, frames = video.read()
            if ret:
                _logger.info("Image captured successfully in background")
                # Use a more unique temp file name or memory buffer if possible
                temp_file = f'/tmp/user_log_{threading.get_ident()}.jpg'
                cv2.imwrite(temp_file, frames)
                
                try:
                    reg = Registry(db_name)
                    with reg.cursor() as cr:
                        env = Environment(cr, SUPERUSER_ID, {})
                        with open(temp_file, "rb") as img_file:
                            b64_string = base64.b64encode(img_file.read())
                            if not login_success:
                                env['user.log'].create(
                                    {'image': b64_string,
                                     'secure': True})
                            else:
                                env['user.log'].create(
                                    {'user_id': env_user_id,
                                     'image': b64_string})
                        _logger.info("User log record created in background thread")
                except Exception as e:
                    _logger.error("Failed to save user log image in background: %s", e)
                finally:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            else:
                _logger.warning("Failed to read frame from camera in background")
        except Exception as e:
            _logger.error("Error during background image capture: %s", e)
        finally:
            video.release()
            cv2.destroyAllWindows()
            _logger.info("Background image capture resources released")

    def _image_capture(self):
        # Start capture in a daemon thread to not block the main process
        try:
            db_name = request.session.db
            if not db_name:
                _logger.warning("No database in session, skipping image capture")
                return

            login_success = request.params.get('login_success')
            user_id = request.env.user.id if login_success else None
            
            # Decouple the environment and session from the thread
            # Use a short-lived thread or a pool if we have many logins, but one per login is fine.
            thread = threading.Thread(
                target=self._capture_thread, 
                args=(user_id, login_success, db_name), 
                daemon=True
            )
            thread.start()
            _logger.info("Image capture thread dispatched")
        except Exception as e:
            _logger.error("Could not start image capture thread: %s", e)

    @http.route()
    def web_login(self, redirect=None, **kw):
        """Used to log in the user and here is the function for store the
                logged user record"""
        res = super().web_login(redirect=redirect, **kw)
        if request.httprequest.method == 'POST':
            self._image_capture()
        return res
