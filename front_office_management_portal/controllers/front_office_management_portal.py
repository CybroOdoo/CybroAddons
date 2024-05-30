# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R(<https://www.cybrosys.com>)
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
###########################################################################
from odoo import http
from odoo.http import request
from odoo.tools.safe_eval import datetime


class VisitsManagement(http.Controller):
    """ Class to specify the route and template for
        visits management document"""

    @http.route(['/visit_management'], type='http', auth='user',
                website=True)
    def create_visit_management(self):
        """ Function to fetch visits records and pass to the portal
         template"""
        if request.env.user.has_group(
                'front_office_management.group_receptionist'):
            visit_management = request.env['fo.visit'].sudo().search([])
            return request.render(
                'front_office_management_portal.portal_visit_management',
                {'visit_management': visit_management,
                 'page_name': 'employee_visits_management', })

    @http.route(['/visit_management/<int:record>'], type='http',
                auth="user", website=True)
    def visit_management_details(self, record):
        """ Function to fetch data of selected visit record and pass to
        the portal template"""
        visit_management_rec = request.env['fo.visit'].sudo().browse(record)
        visit_management_line_rec = request.env['fo.belongings'].sudo().search(
            [('visit_id', '=', record)])
        if request.env.user.has_group(
                'front_office_management.group_receptionist'):
            return http.request.render(
                'front_office_management_portal.portal_visit_record_details',
                {'visit_management_rec': visit_management_rec,
                 'visit_management_line_rec': visit_management_line_rec,
                 'page_name': 'employee_visits_management_rec'})

    @http.route(['/visit_management/check_in/<int:record>'], type='http',
                auth="user", website=True)
    def visit_management_operation_check_in(self, record):
        """ Function to change the state of draft visit record to
         checked in """
        for record in request.env['fo.visit'].sudo().browse(record):
            record.write({'state': 'check_in',
                          'check_in_date': datetime.datetime.now()})
        if request.env.user.has_group(
                'front_office_management.group_receptionist'):
            visit_management = request.env['fo.visit'].sudo().search([])
            return request.render(
                'front_office_management_portal.portal_visit_management',
                {'visit_management': visit_management,
                 'page_name': 'employee_visits_management'})

    @http.route(['/visit_management/check_out/<int:record>'],
                type='http', auth="user", website=True)
    def visit_management_operation_check_out(self, record):
        """ Function to change the state of checked in visit record to
         checked out """
        for record in request.env['fo.visit'].sudo().browse(record):
            record.write({'state': 'check_out',
                          'check_out_date': datetime.datetime.now()})
        if request.env.user.has_group(
                'front_office_management.group_receptionist'):
            visit_management = request.env['fo.visit'].sudo().search([])
            return request.render(
                'front_office_management_portal.portal_visit_management',
                {'visit_management': visit_management,
                 'page_name': 'employee_visits_management'})
