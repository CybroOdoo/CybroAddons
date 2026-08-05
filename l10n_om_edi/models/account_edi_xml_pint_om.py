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
from datetime import datetime, timezone
from typing import Literal
from odoo import models, _


class AccountEdiXmlPint_Om(models.AbstractModel):
    """ Omani implementation of Peppol International (PINT) model for Billing.

    * PINT Official documentation: https://docs.peppol.eu/poac/pint/pint/
    * Oman "Fawtara" e-invoicing program uses a 5-corner Peppol model. Corners 1-4 (this XML) travel the
      Peppol network as usual; Corner 5 (the Oman Tax Authority) instead receives a separate Tax Data
      Document (TDD, urn:peppol:taxdata:om-1) built by l10n_om_edi - not this UBL document.
    * Oman has no clearance/signing step by the tax authority, unlike e.g. Saudi ZATCA: this builder only
      needs to produce a valid Peppol PINT OM document, it does not embed any hash/signature/QR itself.
    """
    _name = 'account.edi.xml.pint_om'
    _inherit = ["account.edi.xml.ubl_bis3"]
    _description = "Omani implementation of Peppol International (PINT) model for Billing"

    def _export_invoice_filename(self, invoice):
        """ Return the PINT OM XML attachment filename for `invoice`. """
        # EXTENDS account_edi_ubl_cii
        return f"{invoice.name.replace('/', '_')}_pint_om.xml"

    def _get_customization_id(self, process_type: Literal['billing', 'selfbilling'] = 'billing'):
        """ Return the PINT OM CustomizationID for a billing or self-billing document. """
        # EXTENDS account_edi_ubl_cii/account.edi.xml.ubl_bis3
        # Also used by `_can_export_selfbilling()` to decide whether self-billing (e.g. import
        # self-invoices) is offered for this format.
        if process_type == 'billing':
            return 'urn:peppol:pint:billing-1@om-1'
        return 'urn:peppol:pint:selfbilling-1@om-1'

    # -------------------------------------------------------------------------
    # EXPORT: Templates
    # -------------------------------------------------------------------------

    def _ubl_add_customization_id_node(self, vals):
        """ Set cbc:CustomizationID to the PINT OM billing/self-billing URN. """
        # EXTENDS account.edi.xml.ubl_bis3
        super()._ubl_add_customization_id_node(vals)
        is_self_billing = self._is_document(vals, 'self_invoice', 'self_credit_note')
        process_type = 'selfbilling' if is_self_billing else 'billing'
        vals['document_node']['cbc:CustomizationID']['_text'] = self._get_customization_id(process_type=process_type)

    def _ubl_add_profile_id_node(self, vals):
        """ Set cbc:ProfileID to the fixed PINT OM billing profile URN. """
        # EXTENDS account.edi.xml.ubl_bis3
        super()._ubl_add_profile_id_node(vals)
        vals['document_node']['cbc:ProfileID']['_text'] = 'urn:peppol:bis:billing'

    def _ubl_add_issue_date_node(self, vals):
        """ Also populate cbc:IssueTime, required by PINT OM (IBT-168) but optional in the generic
        BIS3/EN16931 builder this model inherits from. """
        # EXTENDS account_edi_ubl_cii
        super()._ubl_add_issue_date_node(vals)
        if self._is_document(vals, 'invoice', 'credit_note', 'self_invoice', 'self_credit_note'):
            # Uses the XML generation time, not invoice_date (which has no time component) - matches
            # l10n_my_edi's MyInvois builder for the same requirement.
            vals['document_node']['cbc:IssueTime']['_text'] = datetime.now(timezone.utc).strftime('%H:%M:%S')

    def _ubl_get_partner_address_node(self, vals, partner):
        """ Also add a cac:AddressLine node from `partner.l10n_om_address_line3`, PINT OM's third
        address line (IBT-162), which has no equivalent in Odoo's standard street/street2 model. """
        # EXTENDS account_edi_ubl_cii
        address_node = super()._ubl_get_partner_address_node(vals, partner)
        if partner.l10n_om_address_line3:
            address_node['cac:AddressLine'] = [{'cbc:Line': {'_text': partner.l10n_om_address_line3}}]
        return address_node

    # -------------------------------------------------------------------------
    # EXPORT: Constraints
    # -------------------------------------------------------------------------

    def _export_invoice_constraints(self, invoice, vals):
        """ Add PINT OM-specific export constraints (supplier VAT/CR number, customer Peppol EAS)
        on top of the generic BIS3/EN16931 constraints. """
        # EXTENDS account_edi_ubl_cii
        constraints = super()._export_invoice_constraints(invoice, vals)

        supplier = vals['supplier']
        customer = vals['customer']

        if not supplier.vat:
            constraints['l10n_om_supplier_vat'] = _(
                "The supplier's Oman VAT Identification Number (VATIN) is required to generate a PINT OM invoice."
            )
        if not supplier.commercial_partner_id.l10n_om_cr_number:
            constraints['l10n_om_supplier_cr_number'] = _(
                "The supplier's Oman Commercial Registration (CR) number is required to generate a PINT OM invoice."
            )
        if customer.commercial_partner_id.country_code == 'OM' and customer.peppol_eas != '0248':
            constraints['l10n_om_customer_peppol_eas'] = _(
                "The customer's Peppol e-address scheme should be Oman VAT (0248) for a domestic Oman invoice."
            )

        # NOTE: this is intentionally minimal. Oman's official PINT-OM/TDD schematron (the eventual
        # "BR-OM-*" business rules, by analogy with BR-MY-*/BR-SA-*) is not yet public. Do not add
        # speculative constraints here beyond what's already certain - extend this once the Oman Tax
        # Authority publishes its schematron.
        return constraints
