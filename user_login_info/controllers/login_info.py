# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
"""Controller overriding web login to capture login images."""
import logging
import os
import threading

# pylint: disable=no-name-in-module,broad-exception-caught
from odoo import SUPERUSER_ID, api, http
from odoo.addons.web.controllers.home import Home
from odoo.http import request
from odoo.orm.registry import Registry
from odoo.tools.binary import BinaryBytes

_logger = logging.getLogger(__name__)

# Ensure OpenBLAS does not create multi-threaded workers causing SIGSEGV
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

try:
    import cv2
    cv2.setNumThreads(0)
except ImportError:
    cv2 = None


class ImageController(Home):
    """Controller overriding login endpoint to capture camera images."""

    @classmethod
    def _open_camera(cls):
        """Attempt to open hardware camera safely."""
        if cv2 is None:
            _logger.error("OpenCV (cv2) not available")
            return None

        video = None
        # On Linux, V4L2 is the safest direct camera backend
        try:
            video = cv2.VideoCapture(0, cv2.CAP_V4L2)
        except Exception as err:
            _logger.debug("Could not open camera with CAP_V4L2: %s", err)
            video = None

        if video is None or not video.isOpened():
            _logger.info("Trying default camera backend...")
            try:
                video = cv2.VideoCapture(0)
            except Exception as err:
                _logger.warning("Default camera backend failed: %s", err)
                return None

        if not video.isOpened():
            _logger.warning("Camera could not be opened in thread")
            return None
        return video

    @classmethod
    def _capture_frame(cls, video):
        """Read and encode a single JPEG frame from the camera."""
        if video is None:
            return None
        ret, frames = video.read()
        if not ret or frames is None:
            _logger.warning("Failed to read frame from camera")
            return None

        _logger.info("Image captured successfully in background")
        success, buffer = cv2.imencode('.jpg', frames)
        if not success:
            _logger.warning("Failed to encode captured frame to JPEG")
            return None
        return BinaryBytes(buffer.tobytes())

    @classmethod
    def _save_user_log(cls, db_name, env_user_id, login_success, img_binary):
        """Persist a new user.log record in database."""
        try:
            if isinstance(img_binary, bytes) and not isinstance(
                img_binary, BinaryBytes
            ):
                img_binary = BinaryBytes(img_binary)
            reg = Registry(db_name)
            with reg.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                vals = {
                    'image': img_binary,
                    'secure': not login_success,
                }
                if login_success and env_user_id:
                    vals['user_id'] = env_user_id
                env['user.log'].create(vals)
                _logger.info("User log record created in background thread")
        except Exception as err:
            _logger.error("Failed to save user log image: %s", err)

    def _capture_thread(self, env_user_id, login_success, db_name):
        """Take image when user attempts to login in a separate thread."""
        _logger.info("Background thread started for image capture")
        video = None
        try:
            video = self._open_camera()
            if not video:
                return
            img_binary = self._capture_frame(video)
            if not img_binary:
                return
            self._save_user_log(
                db_name, env_user_id, login_success, img_binary
            )
        except Exception as err:
            _logger.error("Error during background image capture: %s", err)
        finally:
            if video is not None:
                try:
                    video.release()
                except Exception as err:
                    _logger.debug("Could not release video capture: %s", err)
            _logger.info("Background image capture resources released")

    def _image_capture(self):
        """Start capture in a daemon thread to not block the main process."""
        try:
            db_name = request.session.db
            if not db_name:
                _logger.warning("No database in session, skipping capture")
                return

            login_success = bool(request.params.get('login_success'))
            user_id = request.session.uid if login_success else None

            thread = threading.Thread(
                target=self._capture_thread,
                args=(user_id, login_success, db_name),
                daemon=True,
            )
            thread.start()
            _logger.info("Image capture thread dispatched")
        except Exception as err:
            _logger.error("Could not start image capture thread: %s", err)

    @http.route()
    def web_login(self, redirect=None, **kw):
        """Used to log in the user and store the logged user record."""
        res = super().web_login(redirect=redirect, **kw)
        if request.httprequest.method == 'POST':
            self._image_capture()
        return res
