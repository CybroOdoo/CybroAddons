# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.http import request


class DealerMonthlySaleReport(http.Controller):
    """Franchise dealer monthly feedback about the product sale."""

    @http.route(['/feedback_report_menu'], type='http', auth="public",
                website=True)
    def dealer_feedback_form(self, **post):
        """Creating a dealer feedback form in website."""
        franchise_dealer_rec = request.env['res.users'].sudo().search(
            [('is_dealer_user', '=', True)])
        franchise_agreement_rec = request.env[
            'franchise.agreement'].sudo().search([])
        values = {
            'franchise_agreement_rec': franchise_agreement_rec,
            'franchise_dealer_rec': franchise_dealer_rec,
        }
        if post.get('id'):
            values['current_franchise'] = request.env[
                'franchise.dealer'].sudo().browse(
                int(post.get('id')))
        user = request.env['res.users'].sudo().search(
            [('id', '=', int(request.env.user.id))])
        if user.is_dealer_user:
            values['user_data'] = request.env[
                'franchise.dealer'].sudo().search(
                [('dealer_portal_user.id', '=', request.env.user.id)])
        return http.request.render(
            "franchise_management.tmpl_dealer_feedback", values)

    @http.route(['/dealer_feedback_menu/form/submit'], type='http',
                auth="public", website=True)
    def franchise_form_submit(self, **post):
        """Website dealer form submit function."""
        order = request.env['dealer.sale'].sudo().create({
            'dealer_id': post.get('dealer_id'),
            'franchise_reference': post.get('franchise_reference') or '',
            'dealer_agreement_id': post.get('dealer_agreement_id'),
            'sale_quantity': post.get('sale_quantity'),
            'scrap_quantity': post.get('scrap_quantity'),
            'total_sale_amount': post.get('total_sale_amount'),
            'discount_percentage': post.get('discount_percentage'),
            'monthly_target_amount': post.get('monthly_target_amount'),
            'monthly_target_gained': post.get('monthly_target_gained'),
        })
        vals = {'order': order}
        return request.render("franchise_management.feedback_success_page",
                              vals)
