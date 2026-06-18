# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
"""
Controller for handling contact form submissions and redirections
in the Beauty Shop theme.
"""
from odoo import http
from odoo.addons.website.controllers.form import WebsiteForm
from odoo.http import request


class BeautyShopWebsiteForm(WebsiteForm):
    """
    Extended WebsiteForm controller to handle custom beauty shop form logic.
    """

    @http.route('/website/form/<string:model_name>', type='http',
                auth='public', methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        """
        Overrides the standard website form submission to merge first and
        second names into a single name field.
        """
        if 'website_form_signature' not in kwargs:
            kwargs['website_form_signature'] = ''
            if hasattr(request, 'params'):
                request.params['website_form_signature'] = ''
        if 'name' in kwargs and 'second_name' in kwargs:
            full_name = f"{kwargs['name']} {kwargs['second_name']}"
            kwargs['name'] = full_name
            kwargs.pop('second_name', None)
            if hasattr(request, 'params'):
                request.params['name'] = full_name
                request.params.pop('second_name', None)
        return super().website_form(model_name, **kwargs)

    @http.route('/contact/thank-you', type='http', auth='public', website=True)
    def contact_thank_you(self, **kw):
        """
        Renders the custom thank-you page after a successful form submission.
        """
        return request.render('theme_beauty_shop.beauty_shop_contact_thankyou', {})