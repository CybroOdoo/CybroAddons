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
from odoo import http
from odoo.addons.website.controllers.form import WebsiteForm
from odoo.http import request


class BeautyShopWebsiteForm(WebsiteForm):
    """
    Controller for handling website form submissions specifically for the Beauty Shop theme.
    Extends the base WebsiteForm controller to add custom data processing.
    """

    @http.route('/website/form/<string:model_name>', type='http',
                auth='public', methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        """
        Handles the website form submission.
        Specifically, it merges 'name' and 'second_name' fields if both are provided,
        ensuring a full name is passed to the underlying form processing.

        :param str model_name: The name of the Odoo model the form is submitting to.
        :param dict kwargs: The form fields and their values.
        :return: The result of the superclass website_form call.
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
        Renders the custom thank-you page after a successful contact form submission.

        :param dict kw: Optional query parameters.
        :return: A rendered response of the 'theme_beauty_shop.beauty_shop_contact_thankyou' template.
        """
        return request.render('theme_beauty_shop.beauty_shop_contact_thankyou', {})
