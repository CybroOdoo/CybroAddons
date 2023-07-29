# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Lajina (odoo@cybrosys.com)
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
###############################################################################
import base64

from odoo import http
from odoo.http import request


class LegalCaseController(http.Controller):
    """Legal Case Controller"""
    @http.route('/legal/case/register', type="http", auth="user", website=True)
    def legal_case_register(self):
        """ Returns Case Registration Form"""
        return request.render(
            'legal_case_management.legal_case_register_view')

    @http.route('/submit/create/case', type='http', website=True, auth='user')
    def create_case_register(self, **kw):
        """Creation of Cases"""
        attached_files = request.httprequest.files.getlist('attachments')
        case = request.env['case.registration'].sudo().create({
            'client_id': request.env.user.partner_id.id,
            'email': request.env.user.partner_id.email,
            'contact_no': kw['contact'],
            'description': kw['description'],
            'case_category_id': int(kw['case_category']),
            'company_id': request.env.company.id,
        })
        for attachment in attached_files:
            request.env['ir.attachment'].sudo().create({
                'name': attachment.filename,
                'res_model': 'case.registration',
                'res_id': case.id,
                'type': 'binary',
                'datas': base64.b64encode(attachment.read())
            })
        return request.render("legal_case_management.thanks_page")
