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
from odoo.http import request

from odoo.addons.website.controllers.form import WebsiteForm


class VoltroWebsiteForm(WebsiteForm):
    """Merge the first and last name of the Voltro contact form."""

    @http.route()
    def website_form(self, model_name, **kwargs):
        """Join 'name' and 'second_name' into 'name' for 'mail.mail' forms.

        The parent method reads the submitted values from request.params,
        so the values are updated there rather than in kwargs.
        """
        params = request.params
        if model_name == 'mail.mail' and 'name' in params and 'second_name' in params:
            params['name'] = f"{params['name']} {params.pop('second_name')}".strip()
        return super().website_form(model_name, **kwargs)
