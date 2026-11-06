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
from odoo import http
from odoo.http import request


class WebsiteDesk(http.Controller):
    """Ticket form of the website"""

    @http.route(['/helpdesk_ticket'], type='http', auth="public", website=True,
                sitemap=True)
    def helpdesk_ticket(self, **kwargs):
        """Form creating a helpdesk ticket"""
        env = request.env
        products = env['product.template']
        if env['ir.config_parameter'].sudo().get_bool(
                'odoo_website_helpdesk.product_website'):
            products = products.sudo().search([('sale_ok', '=', True)])
        categories = env['helpdesk.category']
        if self._show_category():
            categories = categories.sudo().search([])
        return request.render('odoo_website_helpdesk.ticket_form', {
            'types': env['helpdesk.type'].sudo().search([]),
            'categories': categories,
            'products': products,
        })

    @staticmethod
    def _show_category():
        """Whether the categories are enabled in the settings"""
        category_group = request.env.ref(
            'odoo_website_helpdesk.group_show_category')
        return category_group in request.env.ref(
            'base.group_user').sudo().implied_ids
