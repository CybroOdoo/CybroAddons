# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import io
import qrcode
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home


class PosScreen(Home):
    """The class PosScreen is used for POS specific controller extensions"""

    def _login_redirect(self, uid, redirect=None):
        """Override to add direct login to POS after successful authentication"""
        url = super()._login_redirect(uid, redirect=redirect)
        user = request.env['res.users'].sudo().browse(uid)
        
        # If the user has a POS configuration assigned, redirect them directly
        if user.pos_conf_id:
            # Auto-create the pos.session if it's not already open
            if not user.pos_conf_id.current_session_id:
                request.env['pos.session'].sudo().create({
                    'user_id': user.id,
                    'config_id': user.pos_conf_id.id
                })
            return f'/pos/ui?config_id={user.pos_conf_id.id}'
            
        return url

    @http.route('/pos/qrcode', type='http', auth="user", sitemap=False)
    def pos_qrcode(self, value, **kw):
        """Custom QR code generator to bypass ReportLab/rlPyCairo dependencies"""
        if not value:
            return request.not_found()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(value)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return request.make_response(buffer.getvalue(), headers=[
            ('Content-Type', 'image/png'),
            ('Cache-Control', 'public, max-age=86400')
        ])
