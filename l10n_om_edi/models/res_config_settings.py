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
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.addons.l10n_om_edi.lib.connectors import get_connector_class


class ResConfigSettings(models.TransientModel):
    """ Exposes the company's Oman E-Invoicing ASP configuration on the Settings screen, plus the
    Test Connection action. """
    _inherit = 'res.config.settings'

    l10n_om_edi_asp_provider = fields.Selection(related='company_id.l10n_om_edi_asp_provider', readonly=False)
    l10n_om_edi_asp_required_config = fields.Json(related='company_id.l10n_om_edi_asp_required_config')
    l10n_om_edi_asp_config_status = fields.Selection(related='company_id.l10n_om_edi_asp_config_status')
    l10n_om_edi_asp_config_notes = fields.Char(related='company_id.l10n_om_edi_asp_config_notes')
    l10n_om_edi_asp_ota_accredited = fields.Boolean(related='company_id.l10n_om_edi_asp_ota_accredited')
    l10n_om_edi_asp_base_url = fields.Char(related='company_id.l10n_om_edi_asp_base_url', readonly=False)
    l10n_om_edi_asp_client_id = fields.Char(related='company_id.l10n_om_edi_asp_client_id', readonly=False)
    l10n_om_edi_asp_client_secret = fields.Char(related='company_id.l10n_om_edi_asp_client_secret', readonly=False)
    l10n_om_edi_asp_api_key = fields.Char(related='company_id.l10n_om_edi_asp_api_key', readonly=False)
    l10n_om_edi_asp_username = fields.Char(related='company_id.l10n_om_edi_asp_username', readonly=False)
    l10n_om_edi_asp_password = fields.Char(related='company_id.l10n_om_edi_asp_password', readonly=False)
    l10n_om_edi_asp_certificate_id = fields.Many2one(related='company_id.l10n_om_edi_asp_certificate_id', readonly=False)
    l10n_om_edi_asp_account_id = fields.Char(related='company_id.l10n_om_edi_asp_account_id', readonly=False)
    l10n_om_edi_asp_redirect_url = fields.Char(related='company_id.l10n_om_edi_asp_redirect_url', readonly=False)
    l10n_om_edi_environment = fields.Selection(related='company_id.l10n_om_edi_environment', readonly=False)

    @api.onchange('l10n_om_edi_asp_provider', 'l10n_om_edi_environment')
    def _onchange_l10n_om_edi_asp_provider(self):
        """ Pre-fill the API Base URL when the selected provider's connector declares a known fixed
        host for the chosen environment (see connector.DEFAULT_BASE_URL) - most ASPs issue credentials,
        not a URL, since their API only ever lives at one place. Never overwrites a value the user
        already typed in. """
        if self.l10n_om_edi_asp_base_url:
            return
        connector_cls = self.l10n_om_edi_asp_provider and get_connector_class(self.l10n_om_edi_asp_provider)
        if not connector_cls:
            return
        default_url = connector_cls.DEFAULT_BASE_URL.get(self.l10n_om_edi_environment)
        if default_url:
            self.l10n_om_edi_asp_base_url = default_url

    def action_l10n_om_edi_test_connection(self):
        """ Verify the configured ASP credentials actually authenticate, without touching invoice
        submission. Connectors that don't implement `test_connection` report that plainly rather
        than pretending to test anything. """
        self.check_access('read')
        try:
            connector = self.company_id._l10n_om_edi_get_connector()
        except UserError as e:
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'type': 'danger',
                'message': str(e),
            })
            return

        try:
            connector.test_connection('OM')
        except NotImplementedError:
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'type': 'warning',
                'message': _("%(provider)s's connector does not support a connection test yet.",
                             provider=connector.display_name),
            })
            return
        except UserError as e:
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'type': 'danger',
                'message': str(e),
            })
            return

        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
            'type': 'success',
            'message': _("%(provider)s connection successful!", provider=connector.display_name),
        })
