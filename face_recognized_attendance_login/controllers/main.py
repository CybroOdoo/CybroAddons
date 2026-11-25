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
#############################################################################
import hashlib
import hmac
import time

from odoo import http
from odoo.addons.hr_attendance.controllers.main import HrAttendance
from odoo.http import request


class HrAttendances(HrAttendance):
    """Controller override adding face recognition and secure kiosk check-in."""

    @classmethod
    def _get_employee_photo(cls, employee):
        """Retrieve employee image if valid, excluding SVG initial avatars."""
        image = employee.image_1920 or employee.image_1024 or employee.image_512
        if not image:
            return False
        if (image.mimetype and 'svg' in image.mimetype) or image.content.startswith((b'<?xml', b'<svg')):
            return False
        return image

    @classmethod
    def _get_face_token_secret(cls):
        secret = request.env['ir.config_parameter'].sudo().get_str('database.secret')
        return (secret or 'face_recognition_default_secret').encode('utf-8')

    @classmethod
    def _generate_face_token(cls, employee_id, kiosk_token):
        ts = int(time.time())
        secret = cls._get_face_token_secret()
        message = f"{employee_id}:{kiosk_token}:{ts}".encode('utf-8')
        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        return f"{ts}.{signature}"

    @classmethod
    def _verify_face_token(cls, employee_id, kiosk_token, face_token):
        if not face_token or '.' not in face_token:
            return False
        try:
            ts_str, signature = face_token.split('.', 1)
            ts = int(ts_str)
        except (ValueError, TypeError):
            return False
        # Token valid for 3 minutes from issuance
        if abs(time.time() - ts) > 180:
            return False
        secret = cls._get_face_token_secret()
        message = f"{employee_id}:{kiosk_token}:{ts}".encode('utf-8')
        expected_signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected_signature)

    @http.route('/get_image', type="jsonrpc", auth="public")
    def get_image(self, employee_id, token=None):
        """Returns the employee photo and a verification token for the kiosk."""
        try:
            employee_id = int(employee_id)
        except (ValueError, TypeError):
            return False

        # Validate kiosk token or logged-in internal user
        company = self._get_company(token) if token else False
        if not company and not request.env.user._is_internal():
            return False

        employee = request.env['hr.employee'].sudo().browse(employee_id)
        if not employee.exists():
            return False

        # Ensure employee belongs to the kiosk's company
        if company and employee.company_id != company:
            return False

        image = self._get_employee_photo(employee)
        if not image:
            return False

        face_token = self._generate_face_token(employee.id, token) if token else None
        return {
            'image': image.to_base64(),
            'face_token': face_token,
        }

    @http.route('/hr_attendance/manual_selection', type="jsonrpc", auth="public")
    def manual_selection(self, token, employee_id, pin_code, face_token=None, **kwargs):
        """Override manual_selection to enforce server-side face verification."""
        company = self._get_company(token)
        if company:
            try:
                emp_id = int(employee_id)
            except (ValueError, TypeError):
                return {}
            employee = request.env['hr.employee'].sudo().browse(emp_id)
            # Enforce face token verification if employee has a photo configured
            if self._get_employee_photo(employee):
                if not face_token or not self._verify_face_token(emp_id, token, face_token):
                    return {}
        return super().manual_selection(token, employee_id, pin_code, **kwargs)
