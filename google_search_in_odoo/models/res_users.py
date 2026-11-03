# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Yadhu Shankar E (odoo@cybrosys.com)
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
import logging

from odoo import api, models

try:
    from exa_py import Exa
except ImportError:
    Exa = None

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """Extend res.users to provide systray Google Search methods."""
    _inherit = 'res.users'

    @api.model
    def get_google_search_status(self):
        """Return whether Google Search is enabled in system settings."""
        return bool(self.env['ir.config_parameter'].sudo().get_param(
            'google_search_in_odoo.google_search'
        ))

    @api.model
    def google_search_config(self, input_data):
        """Query the search engine using the user input and return formatted results."""
        if not input_data or not str(input_data).strip():
            return []

        if not self.get_google_search_status():
            return {'error': 'Please enable Google Search.'}

        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'google_search_in_odoo.ser_client_api'
        )
        if not api_key:
            return {'error': 'Please provide API key.'}

        if Exa is None:
            _logger.error("exa-py library is not installed.")
            return {'error': 'Exa library is not installed on the server.'}

        try:
            exa = Exa(api_key.strip())
            response = exa.search(
                str(input_data).strip(),
                num_results=10,
                type="auto",
                contents={"highlights": True}
            )

            items = []
            if response and getattr(response, 'results', None):
                for result in response.results:
                    snippet = ""
                    if getattr(result, 'highlights', None):
                        snippet = " ... ".join(result.highlights)
                    elif getattr(result, 'summary', None):
                        snippet = result.summary
                    elif getattr(result, 'text', None):
                        text = result.text
                        snippet = text[:300] + "..." if len(text) > 300 else text

                    items.append({
                        'title': getattr(result, 'title', '') or '',
                        'link': getattr(result, 'url', '') or '',
                        'snippet': snippet,
                    })
            return items
        except Exception as e:
            _logger.exception("Google search query failed: %s", e)
            return {'error': 'Unable to complete search. Please verify the API key and try again.'}
