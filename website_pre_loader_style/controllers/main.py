# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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


class WebsitePreLoaderStyle(http.Controller):
    """Public endpoints for website pre-loader assets."""

    @http.route('/website_pre_loader_style/loader_config', type='json',
                auth='public', website=True)
    def loader_config(self):
        """Return the loader configuration without requiring a backend session."""
        config = request.env['ir.config_parameter'].sudo()
        enabled = config.get_param(
            'website_pre_loader_style.enable_website_pre_loader', 'True')
        return {
            'enabled': enabled in ('True', 'true', '1'),
            'loader_style': config.get_param(
                'website_pre_loader_style.loader_style', 'dual') or 'dual',
        }
