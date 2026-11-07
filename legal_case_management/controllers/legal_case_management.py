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
        attachment_ids = []
        for attachment in attached_files:
            if attachment and attachment.filename:
                file_content = attachment.read()
                if file_content:
                    att = request.env['ir.attachment'].sudo().create({
                        'name': attachment.filename,
                        'res_model': 'case.registration',
                        'res_id': case.id,
                        'type': 'binary',
                        'raw': file_content,
                    })
                    attachment_ids.append(att.id)
        if attachment_ids and hasattr(case, '_message_log'):
            case._message_log(
                attachment_ids=attachment_ids,
            )
        return request.render("legal_case_management.thanks_page")
