# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
##############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalAccount(CustomerPortal):
    """ Super customer portal and get count of contracts """
    def _prepare_home_portal_values(self, counters):
        """ Prepares values for the home portal """
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id.id
        contract_count = request.env['subscription.contracts'].search([
            ('partner_id', '=', partner)])
        values['contract_count'] = len(contract_count)
        return values


class ContractsController(http.Controller):
    """ Sale contract in customer portal controller """
    @http.route(['/my/contracts'], type='http', auth='user', csrf=False,
                website=True)
    def portal_my_quotes(self):
        """ Displays Contracts in portal """
        partner = request.env.user.partner_id.id
        values = {
            'records': request.env['subscription.contracts'].search(
                [('partner_id', '=', partner)]),
        }
        return request.render(
            'sales_contract_and_recurring_invoices.tmp_contract_details', values)

    @http.route(['/contracts/<int:contract_id>/'], type='http', auth='user',
                csrf=False, website=True)
    def portal_manufacture(self, contract_id):
        """ Customer portal subscription contract """
        values = {
            'records': request.env['subscription.contracts'].browse(
                contract_id),
        }
        return request.render(
            'sales_contract_and_recurring_invoices.contract_details', values)

    @http.route(['/report/pdf/<int:contract_id>/'], type='http', auth='user',
                csrf=False, website=True)
    def action_print_report(self, contract_id):
        """ Print subscription contract report """
        data = {
            'records': request.env['subscription.contracts'].browse(contract_id)
        }
        report = request.env.ref(
            'sales_contract_and_recurring_invoices.action_report_subscription_contracts')
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'sales_contract_and_recurring_invoices.action_report_subscription_contracts',
            [report.id], data=data)[0]
        pdfhttpheaders = [('Content-Type', 'application/pdf'),
                          ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)
