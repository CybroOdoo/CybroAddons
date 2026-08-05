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
import functools
import re

from odoo import models, fields, api
from odoo.addons.account_edi_ubl_cii.models.account_edi_common import EAS_MAPPING
from odoo.addons.account_edi_ubl_cii.models.res_partner import ResPartner as _CoreResPartner
from odoo.addons.base_vat.models.res_partner import _ref_vat

# Not to be confused with '0242', the Peppol Service Provider Identification Scheme - that
# identifies Peppol service providers, not end taxpayers.
EAS_MAPPING['OM'] = {'0248': 'vat'}

# `EAS_MAPPING` is a single dict shared by every database served by this Odoo process, not
# something scoped per database. Once this module has been imported once (e.g. an earlier install
# on another database, without a server restart in between), '0248' stays in EAS_MAPPING['OM'] for
# the rest of the process's life - including for a *different*, later-loaded database that doesn't
# have l10n_om_edi installed and so never added '0248' to its own `peppol_eas` selection. Core's
# `_compute_peppol_eas` (account_edi_ubl_cii) would then try to assign a code that isn't valid in
# that other database's registry and raise, breaking every write to res.partner there.
#
# A normal `_inherit` override here can't protect that other database - Odoo only mixes this
# module's classes into a database's registry when l10n_om_edi is actually installed there, and in
# that case '0248' is always valid anyway. Patching the shared core method directly is the only way
# a fix confined to this file can reach it, and it's guaranteed to be in place whenever the leak
# could occur, since both happen on the same import of this module.
_super_compute_peppol_eas = _CoreResPartner._compute_peppol_eas


@functools.wraps(_super_compute_peppol_eas)
def _compute_peppol_eas_leak_safe(self):
    for partner in self:
        try:
            _super_compute_peppol_eas(partner)
        except ValueError:
            partner.peppol_eas = False


_CoreResPartner._compute_peppol_eas = _compute_peppol_eas_leak_safe

_ref_vat['om'] = "OM1234567890"

_check_vat_om_re = re.compile(r"^OM\d{10}$")


class ResPartner(models.Model):
    """ Adds Oman-specific partner fields (CR number, address line 3) and wires up the PINT OM
    EDI format, Oman VAT Peppol EAS, and Oman VATIN format check. """
    _inherit = 'res.partner'

    invoice_edi_format = fields.Selection(selection_add=[('pint_om', "Oman (Peppol PINT OM)")])
    peppol_eas = fields.Selection(selection_add=[('0248', "Oman VAT")])
    l10n_om_cr_number = fields.Char(
        string="CR Number",
        help="Oman Commercial Registration (CR) number, as issued by the Ministry of Commerce, "
             "Industry and Investment Promotion (MOCIIP).",
    )
    l10n_om_address_line3 = fields.Char(
        string="Address Line 3",
        help="A third address line, confirmed as a real PINT-OM business term (IBT-162, 'Seller/Buyer "
             "address line 3') by both Flick Network's live sandbox validator (a real submission "
             "rejected without it) and Fynamics' documented API schema (their 'PostalAddress."
             "AddressLine3' field) - independent of Odoo's standard 2-line street/street2 address "
             "model, which has no equivalent third line.",
    )

    def _get_edi_builder(self, invoice_edi_format):
        """ Return the PINT OM builder model for the 'pint_om' EDI format. """
        # EXTENDS 'account_edi_ubl_cii'
        if invoice_edi_format == 'pint_om':
            return self.env['account.edi.xml.pint_om']
        return super()._get_edi_builder(invoice_edi_format)

    def _get_ubl_cii_formats_info(self):
        """ Register 'pint_om' as a valid Peppol format for Oman, not yet reachable through Odoo's
        own access point. """
        # EXTENDS 'account_edi_ubl_cii'
        formats_info = super()._get_ubl_cii_formats_info()
        formats_info['pint_om'] = {'countries': ['OM'], 'on_peppol': False}
        return formats_info

    @api.model
    def _commercial_fields(self):
        """ Propagate the CR number from a commercial partner to its child contacts. """
        return super()._commercial_fields() + ['l10n_om_cr_number']

    def check_vat_om(self, vat):
        """ Format-only check: 'OM' followed by 10 digits. No checksum algorithm is validated here -
        the ISO 7064 MOD 11-2 scheme sometimes cited for this isn't from an official OTA source, and a
        wrong checksum would reject genuinely valid VATINs. """
        return bool(_check_vat_om_re.match(vat))
