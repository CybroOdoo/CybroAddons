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
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.addons.l10n_om_edi.lib.connectors import get_connector_class
from odoo.addons.l10n_om_edi.lib.connectors.base import CONFIG_STATUS_SELECTION

# Keep in sync with the connector modules registered in lib/connectors/__init__.py. Oman's e-invoicing
# mandate allows multiple Accredited Service Providers (unlike e.g. Malaysia's single MyInvois portal),
# so this is a plain per-company choice rather than a hardcoded single integration. This is the
# complete, official OTA Accredited Service Provider list - see
# https://fawtara.taxoman.gov.om/accredited-service-providers.
ASP_PROVIDER_SELECTION = [
    ('cleartax', "ClearTax"),
    ('jsr', "JSR Tax Advisors"),
    ('flick', "Flick Network"),
    ('smarteis', "SMARTeIS"),
    ('convergex', "ConvergeX"),
    ('bdo', "BDO"),
    ('cygnet', "Cygnet"),
    ('fynamics', "Fynamics"),
    ('webtel', "Webtel"),
    ('faturathi', "Faturathi"),
    ('marminai', "Marmin AI"),
    ('goroute', "GoRoute"),
]


class ResCompany(models.Model):
    """ Stores the company's chosen Oman e-invoicing ASP and its credentials, and exposes the
    single seam (`_l10n_om_edi_get_connector`) a real ASP integration is wired in through. Also
    exposes the company's Oman CR number and PINT OM address line 3, related from its partner. """
    _inherit = 'res.company'

    l10n_om_cr_number = fields.Char(related='partner_id.l10n_om_cr_number', readonly=False)
    l10n_om_address_line3 = fields.Char(related='partner_id.l10n_om_address_line3', readonly=False)

    l10n_om_edi_asp_provider = fields.Selection(
        selection=ASP_PROVIDER_SELECTION,
        string="ASP Provider",
        help="The Accredited Service Provider (ASP) this company has contracted, via the Fawtara "
             "Portal, to submit e-invoices to the Oman Tax Authority.",
    )
    # Provider-driven config metadata, computed from the selected connector class - see
    # lib/connectors/base.py and _compute_l10n_om_edi_asp_config_meta below.
    l10n_om_edi_asp_required_config = fields.Json(
        string="ASP Required Configuration",
        compute='_compute_l10n_om_edi_asp_config_meta',
    )
    l10n_om_edi_asp_config_status = fields.Selection(
        selection=CONFIG_STATUS_SELECTION,
        string="ASP Config Confidence",
        compute='_compute_l10n_om_edi_asp_config_meta',
        help="How well the shown configuration fields are actually verified against the selected "
             "provider's own documentation - see the note below the ASP Provider field.",
    )
    l10n_om_edi_asp_config_notes = fields.Char(
        string="ASP Config Notes",
        compute='_compute_l10n_om_edi_asp_config_meta',
    )
    l10n_om_edi_asp_ota_accredited = fields.Boolean(
        string="ASP is OTA-Accredited",
        compute='_compute_l10n_om_edi_asp_config_meta',
        help="Whether the selected provider actually appears on the Oman Tax Authority's own "
             "published accredited-provider list - the real, legal answer to whether this ASP can be "
             "used for Oman e-invoicing at all, independent of how well its API happens to be "
             "documented.",
    )

    l10n_om_edi_asp_base_url = fields.Char(string="ASP API Base URL")
    l10n_om_edi_asp_client_id = fields.Char(string="ASP Client ID")
    l10n_om_edi_asp_client_secret = fields.Char(string="ASP Client Secret", groups='base.group_system')
    l10n_om_edi_asp_api_key = fields.Char(string="ASP API Key", groups='base.group_system')
    l10n_om_edi_asp_username = fields.Char(string="ASP Username")
    l10n_om_edi_asp_password = fields.Char(string="ASP Password", groups='base.group_system')
    l10n_om_edi_asp_certificate_id = fields.Many2one(
        comodel_name='certificate.certificate', string="ASP Client Certificate",
    )
    l10n_om_edi_asp_account_id = fields.Char(
        string="ASP Account / Tenant / Company ID",
        help="Some ASPs require a sub-account identifier alongside the credentials above "
             "(e.g. Pagero's 'companyId').",
    )
    l10n_om_edi_asp_redirect_url = fields.Char(
        string="ASP OAuth Redirect URL",
        help="Required by ASPs using an OAuth2 authorization_code flow - must be pre-registered with "
             "the provider.",
    )
    l10n_om_edi_environment = fields.Selection(
        selection=[('test', "Sandbox"), ('production', "Production")],
        string="ASP Environment",
        default='test',
        required=True,
    )

    @api.depends('l10n_om_edi_asp_provider')
    def _compute_l10n_om_edi_asp_config_meta(self):
        """ Surface the selected connector's REQUIRED_CONFIG/CONFIG_STATUS/CONFIG_NOTES/OTA_ACCREDITED
        class attributes as company fields, so the Settings view can read them. """
        for company in self:
            connector_cls = company.l10n_om_edi_asp_provider and get_connector_class(company.l10n_om_edi_asp_provider)
            if connector_cls:
                company.l10n_om_edi_asp_required_config = connector_cls.REQUIRED_CONFIG
                company.l10n_om_edi_asp_config_status = connector_cls.CONFIG_STATUS
                company.l10n_om_edi_asp_config_notes = connector_cls.CONFIG_NOTES
                company.l10n_om_edi_asp_ota_accredited = connector_cls.OTA_ACCREDITED
            else:
                company.l10n_om_edi_asp_required_config = []
                company.l10n_om_edi_asp_config_status = False
                company.l10n_om_edi_asp_config_notes = False
                company.l10n_om_edi_asp_ota_accredited = False

    def _l10n_om_edi_get_connector(self, timeout_limit=None):
        """ Return an instantiated connector for this company's configured ASP provider.

        This is the single seam a real ASP integration is wired in through: once a provider's
        connector (lib/connectors/<vendor>.py) implements `submit_invoice`/`get_status`/`cancel` for
        real, no other code in this module needs to change.
        """
        self.ensure_one()
        if not self.l10n_om_edi_asp_provider:
            raise UserError(_(
                "No Accredited Service Provider is configured for %(company)s. "
                "Go to Settings > Accounting > Oman E-Invoicing to select one.",
                company=self.display_name,
            ))
        connector_cls = get_connector_class(self.l10n_om_edi_asp_provider)
        if not connector_cls:
            raise UserError(_(
                "%(provider)s has no working integration yet - only Flick Network is currently "
                "implemented. Contact %(provider)s directly to arrange API access, or submit invoices "
                "manually in the meantime using the generated PINT OM invoice and Tax Data Document XML.",
                provider=dict(self._fields['l10n_om_edi_asp_provider'].selection).get(self.l10n_om_edi_asp_provider),
            ))

        return connector_cls(
            base_url=self.l10n_om_edi_asp_base_url,
            client_id=self.l10n_om_edi_asp_client_id,
            client_secret=self.l10n_om_edi_asp_client_secret,
            api_key=self.l10n_om_edi_asp_api_key,
            username=self.l10n_om_edi_asp_username,
            password=self.l10n_om_edi_asp_password,
            certificate_id=self.l10n_om_edi_asp_certificate_id,
            account_id=self.l10n_om_edi_asp_account_id,
            redirect_url=self.l10n_om_edi_asp_redirect_url,
            environment=self.l10n_om_edi_environment,
            timeout_limit=timeout_limit,
        )


class BaseDocumentLayout(models.TransientModel):
    """ Exposes the company's Oman CR number to the document layout preview/config wizard. """
    _inherit = 'base.document.layout'

    account_fiscal_country_id = fields.Many2one(related="company_id.account_fiscal_country_id")
    l10n_om_cr_number = fields.Char(related='company_id.l10n_om_cr_number')
