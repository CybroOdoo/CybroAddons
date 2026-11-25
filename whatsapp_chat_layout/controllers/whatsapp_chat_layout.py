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
import base64
from odoo import http
from odoo.http import request


def _to_base64_str(value):
    """Convert binary field value to base64 string."""
    if not value:
        return False
    if hasattr(value, 'to_base64'):
        return value.to_base64()
    if isinstance(value, (bytes, bytearray, memoryview)):
        return base64.b64encode(value).decode('ascii')
    if isinstance(value, str):
        return value
    return False


class Color(http.Controller):
    """Controller providing WhatsApp chat theme settings for Discuss."""

    @http.route('/select_color', auth='public', type='jsonrpc')
    def get_color(self, **kwargs):
        """Return configured background color, layout color, and company background image."""
        ICP = request.env['ir.config_parameter'].sudo()
        background_color = ICP.get_str('whatsapp_chat_layout.background_color') or '#ECE5DD'
        layout_color = ICP.get_str('whatsapp_chat_layout.layout_color') or '#00A884'

        company = getattr(request.env, 'company', None) or request.env.user.company_id
        background_image = False
        if company and company.background_image:
            background_image = _to_base64_str(company.background_image)

        return {
            'background_color': background_color,
            'layout_color': layout_color,
            'background_image': background_image,
        }

    @http.route('/select_user_image', auth='public', type='jsonrpc')
    def get_user_image(self, **kwargs):
        """Return current user partner avatar image in base64."""
        user = getattr(request.env, 'user', None)
        if user and user.partner_id and user.partner_id.image_1920:
            return _to_base64_str(user.partner_id.image_1920)
        return False
