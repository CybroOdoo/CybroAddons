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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    """Zendesk connection settings (OAuth 2.0 client credentials) and the
    Test Connection button"""
    _inherit = 'res.config.settings'

    is_connect_zendesk = fields.Boolean(
        string="Connect Zendesk",
        help="Do you want to connect with Zendesk?",
        config_parameter='odoo_zendesk_connector.is_connect_zendesk')
    company_domain = fields.Char(
        string='Company Domain',
        help="Your Zendesk subdomain, e.g. 'mycompany' for "
             "https://mycompany.zendesk.com",
        config_parameter='odoo_zendesk_connector.company_domain')
    zendesk_client_id = fields.Char(
        string='OAuth Client Identifier',
        help="The 'Identifier' of the OAuth client created in Zendesk "
             "Admin Center > Apps and integrations > APIs > OAuth clients",
        config_parameter='odoo_zendesk_connector.client_id')
    zendesk_client_secret = fields.Char(
        string='OAuth Client Secret',
        help="The secret shown when the OAuth client was created",
        config_parameter='odoo_zendesk_connector.client_secret')
    zendesk_scope = fields.Char(
        string='OAuth Scope', default='read write',
        help="Space separated scopes, e.g. 'read write'",
        config_parameter='odoo_zendesk_connector.scope')

    def set_values(self):
        """Drop the cached access token whenever the credentials change, so
        the next call fetches a token for the new client."""
        params = self.env['ir.config_parameter'].sudo()
        old = (params.get_str('odoo_zendesk_connector.company_domain'),
               params.get_str('odoo_zendesk_connector.client_id'),
               params.get_str('odoo_zendesk_connector.client_secret'),
               params.get_str('odoo_zendesk_connector.scope'))
        res = super().set_values()
        new = (self.company_domain or False, self.zendesk_client_id or False,
               self.zendesk_client_secret or False,
               self.zendesk_scope or False)
        if tuple(v or False for v in old) != new:
            self.env['zendesk.api']._clear_token()
        return res

    def action_test_connection(self):
        """Check whether the connection is established or not"""
        self.ensure_one()
        zendesk = self.env['zendesk.api']
        if not self.is_connect_zendesk:
            return zendesk.notify(
                _('Error'),
                _("Please enable 'Connect Zendesk' first."),
                'danger')
        # Test with the values currently on screen (even before saving)
        config = {
            'domain': (self.company_domain or '').strip(),
            'client_id': (self.zendesk_client_id or '').strip(),
            'client_secret': (self.zendesk_client_secret or '').strip(),
            'scope': (self.zendesk_scope or 'read write').strip(),
        }
        if not all((config['domain'], config['client_id'],
                    config['client_secret'])):
            return zendesk.notify(
                _('Error'),
                _("Please fill in the Company Domain, OAuth "
                  "Client Identifier and Secret."),
                'danger')
        try:
            self.set_values()
            zendesk._fetch_access_token(config)
            zendesk._request('GET', 'tickets.json', params={'per_page': 1})
        except UserError as error:
            return zendesk.notify(_('Error'), str(error), 'danger')
        return zendesk.notify(_("Connection Test Succeeded!"),
                              _("Everything seems properly set up!"),
                              'success')
