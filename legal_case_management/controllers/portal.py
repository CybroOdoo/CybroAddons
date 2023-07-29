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
from odoo.addons.portal.controllers.portal import CustomerPortal

from odoo import http
from odoo.http import request


class PortalLegalCase(CustomerPortal):
    """Customer Portal"""

    def _prepare_home_portal_values(self, counters):
        """Returns the portal values"""
        values = super()._prepare_home_portal_values(counters)
        if 'case_count' in counters:
            values['case_count'] = request.env[
                'case.registration'].sudo().search_count(
                [('state', '!=', 'invoiced'),
                 ('client_id.id', '=', request.env.user.partner_id.id)]) \
                if request.env['case.registration'].sudo(). \
                check_access_rights('read', raise_exception=False) else 0
        return values

    @http.route('/my/legal/case',
                type='http', auth="user", website=True)
    def legal_cases(self):
        """Returns the case Records"""
        records = request.env['case.registration'].sudo(). \
            search([('client_id', '=', request.env.user.partner_id.id)])
        values = {
            'records': records,
            'page_name': 'case'
        }
        return request.render(
            "legal_case_management.portal_my_legal_case_requests",
            values)

    @http.route(['/my/cases/<int:case_id>'], type='http', auth="public",
                website=True)
    def portal_my_details_detail(self, case_id):
        """ Returns the Portal details"""
        case_record = request.env['case.registration'].sudo().browse(case_id)
        evidences = request.env['legal.evidence'].sudo().search(
            [('client_id', '=', case_record.client_id.id),
             ('case_id', '=', case_record.id)])
        trials = request.env['legal.trial'].sudo().search(
            [('client_id', '=', case_record.client_id.id),
             ('case_id', '=', case_record.id)])
        records = {
            'case_record': case_record,
            'evidence': evidences,
            'trial': trials,
            'page_name': 'case'
        }
        return request.render("legal_case_management.portal_legal_case_page",
                              records)
