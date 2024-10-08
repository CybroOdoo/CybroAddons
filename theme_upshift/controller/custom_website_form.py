# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: FATHIMA SHALFA P (odoo@cybrosys.com)
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
#############################################################################
from odoo import http
from odoo.addons.website.controllers.form import WebsiteForm

class CustomWebsiteForm(WebsiteForm):
    """
    This class extends the WebsiteForm controller in Odoo to allow custom handling
    of form submissions from the website. Specifically, it modifies form submissions
    for the 'mail.mail' model to concatenate the 'name' and 'second_name' fields
    into a single 'name' field before processing the form.
    """
    @http.route('/website/form/<string:model_name>', type='http',
                auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        """
        If the model is 'mail.mail' and the fields 'name' and 'second_name' are
        provided, it concatenates these two fields into the 'name' field.
        """
        if model_name == 'mail.mail':
            if 'name' in kwargs and 'second_name' in kwargs:
                kwargs['name'] = f"{kwargs['name']} {kwargs['second_name']}"
                kwargs.pop('second_name', None)
        return super(CustomWebsiteForm, self).website_form(model_name, **kwargs)