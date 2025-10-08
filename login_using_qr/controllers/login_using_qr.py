# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjhana A K (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import Controller, request


class LoginController(Controller):
    """Controller that works when Login With QR clicked"""

    @http.route(['/web/redirect'], type='json', auth='none', website=True,
                csrf=False, csrf_token=None)
    def scanner(self, scanned_qr):
        """This code scans the QR provided and Login to the corresponding user
        note: Only Internal User can log in through it"""
        users = request.env['res.users'].sudo().search([('share', '=', False)])
        login = users.mapped('login')
        if scanned_qr in login:
            request.session.authenticate_without_passwd(
                            request.session.db, scanned_qr)
            return request.redirect('/')
        else:
            return False
