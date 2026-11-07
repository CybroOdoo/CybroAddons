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
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http
from odoo.http import request


class PortalLegalCase(CustomerPortal):
    """Customer Portal"""
    def _prepare_portal_counter_values(self, counter):
        """Returns the portal values"""
        if counter == 'case_count':
            partner = request.env.user.partner_id
            return 'case.registration', [('state', '!=', 'invoiced'), ('client_id.id', '=', partner.id)], 'read'
        return super()._prepare_portal_counter_values(counter)

    @http.route('/my/legal/case',
                type='http', auth="user", website=True)
    def legal_cases(self):
        """Returns the case Records"""
        records = request.env['case.registration'].search(
            [('client_id', '=', request.env.user.partner_id.id)])
        values = {
            'records': records,
            'page_name': 'case'
        }
        return request.render(
            "legal_case_management.portal_my_legal_case_requests",
            values)

    @http.route(['/my/cases/<int:case_id>'], type='http', auth="user",
                website=True)
    def portal_my_details_detail(self, case_id):
        """ Returns the Portal details"""
        case_record = request.env['case.registration'].browse(case_id)
        if not case_record.exists():
            return request.redirect('/my')
        if not request.env.user.has_group('base.group_user'):
            partner = request.env.user.partner_id
            if case_record.client_id != partner and partner not in case_record.client_id.child_ids:
                return request.redirect('/my')
        evidences = request.env['legal.evidence'].sudo().search(
            [('case_id', '=', case_record.id)])
        trials = request.env['legal.trial'].sudo().search(
            [('case_id', '=', case_record.id)])
        records = {
            'case_record': case_record,
            'evidence': evidences,
            'trial': trials,
            'page_name': 'case'
        }
        return request.render("legal_case_management.portal_legal_case_page",
                              records)
