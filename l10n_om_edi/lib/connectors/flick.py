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
import json
from datetime import datetime, timezone

from odoo import _
from odoo.exceptions import UserError

from .base import L10nOmEdiConnector, register_connector


@register_connector('flick')
class FlickNetworkConnector(L10nOmEdiConnector):
    """ Flick Network connector.

    OTA-accredited (legal entity "Advanced Information Technology Company LLC", contact
    ameen@flick.network). API reference: developer.flick.network/api-references/regional/om.

    - Sandbox server: https://sb-om-api.flick.network (production host not yet published).
    - Auth: static API key via `X-Flick-Auth-Key` (implemented here). They also document an OAuth2
      client_credentials flow (POST /v1/oauth/token), not implemented here.
    - `GET /v1/auth/verify` -> {"status", "message", "data": null}, implemented as test_connection().
    - Before any document can be submitted, the company must be registered as a "Participant" on
      Flick's Peppol network (POST /v1/participants, a one-time manual setup via their dashboard, not
      something this connector does). The resulting `participant_id` maps onto this module's generic
      `account_id` slot and is required on every call below.
    - `POST /v1/{participant_id}/documents` accepts their own flattened PINT-OM JSON schema or XML.
      JSON is used here instead of the generic PINT-OM XML because their validator expects Peppol IDs
      as a combined "scheme:value" string (e.g. "0248:OM1234567890"), not the standard XML
      schemeID-attribute convention - see `_build_flick_payload`. `invoice_xml`/`tdd_xml` are still
      always generated and kept as attachments (Oman's 10-year self-archival requirement), just not
      transmitted to Flick. The request body must be wrapped in a top-level "document" key - required
      but not shown in their sample payload. Response on success: {"status": "success", "data":
      {"document_id"/"id", "status", "exchange_status", "reporting_status"}}; on failure: {"status":
      "failed", "data": {"errors": [...]}}  or errors at the top level - `_format_flick_error` handles
      both documented and undocumented error-entry shapes rather than guessing further.
      `tdd_xml` is accepted (shared connector interface) but unused: Flick performs Corner-5/OTA
      reporting itself once the invoice is submitted.
    - `item_type` (BTOM-013, "MUST be provided except for simplified invoices") has only one example
      value in their docs ("GS") and no enum list - defaulted to "GS" for every line, pending
      clarification from Flick on the real allowed values.
    - `GET /v1/{participant_id}/documents/{document_id}` reuses the same status envelope, implemented
      as get_status().
    - No cancel/void endpoint is documented (only "Retry Document") - consistent with Oman/Peppol
      generally correcting via credit notes, already how l10n.om.edi.document works.
    """
    display_name = "Flick Network"
    OTA_ACCREDITED = True
    REQUIRED_CONFIG = ['api_key', 'account_id']
    CONFIG_STATUS = 'confirmed'
    DEFAULT_BASE_URL = {
        'test': 'https://sb-om-api.flick.network',
        # Production host not yet seen (their docs page may offer a server switcher) - leave unset
        # rather than guess a naming pattern (e.g. dropping the "sb-" prefix).
    }
    CONFIG_SOURCE = "https://developer.flick.network/api-references/regional/om"
    CONFIG_NOTES = ("Officially OTA-accredited for Oman (Data Residency: Oman; contact "
                     "ameen@flick.network). Confirmed: static API key via 'X-Flick-Auth-Key' (sandbox "
                     "server pre-filled above), plus an 'Account / Tenant / Company ID' field that "
                     "must hold your Flick 'participant_id' - you must first register as a Participant "
                     "via the Flick dashboard/API before any document call works. Authentication, "
                     "connectivity check, invoice submission and status polling are all implemented; "
                     "only cancellation has no documented endpoint yet.")

    # -------------------------------------------------------------------------
    # Real, confirmed calls
    # -------------------------------------------------------------------------

    def test_connection(self, country_code):
        """ GET /v1/auth/verify - confirmed side-effect-free way to check the configured API key is
        valid, without touching invoice submission at all. """
        if not self.api_key:
            raise self._not_configured_error()
        return self._request(
            'GET', '/v1/auth/verify',
            headers={'X-Flick-Auth-Key': self.api_key},
        )

    def submit_invoice(self, invoice_xml, tdd_xml, document):
        """ POST /v1/{participant_id}/documents, submitting Flick's own documented JSON schema built
        from the invoice record - see class docstring for why JSON was chosen over reusing the
        generic XML. `tdd_xml` is unused: Flick performs Corner-5/OTA reporting itself from the
        submitted invoice. """
        if not self.account_id:
            raise UserError(_(
                "No Flick 'participant_id' is configured (Account / Tenant / Company ID field). "
                "Register your company as a Participant via the Flick dashboard first, then enter "
                "the resulting participant_id in Settings > Accounting > Oman E-Invoicing."
            ))
        payload = self._build_flick_payload(document)
        response = self._request(
            'POST', f'/v1/{self.account_id}/documents',
            json={'document': payload},
            headers={'X-Flick-Auth-Key': self.api_key},
            handle_response=False,
        )
        return self._handle_submit_response(response)

    def _build_flick_payload(self, document):
        """ Maps `document`/`document.move_id` into Flick's JSON schema (see class docstring). Reuses
        the pint_om EDI builder's tax-category/UN-ECE unit-code logic rather than re-deriving it. """
        move = document.move_id
        builder = move.env['account.edi.xml.pint_om']
        supplier = move.company_id.partner_id.commercial_partner_id
        customer = move.partner_id.commercial_partner_id
        # In Odoo 19, a genuine product line has display_type == 'product' (not a falsy value as in
        # older versions) - section/note/tax/payment-term lines have their own distinct display_type.
        lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')

        def _party(partner):
            peppol_value = partner.peppol_endpoint or partner.vat
            return {
                'legal_name': partner.name,
                'trade_name': partner.name,
                'peppol_id': f"{partner.peppol_eas}:{peppol_value}" if partner.peppol_eas and peppol_value else None,
                'vat_number': partner.vat,
                'street_address': partner.street,
                'additional_street_address': partner.street2,
                'additional_address_lines': [partner.l10n_om_address_line3] if partner.l10n_om_address_line3 else [],
                'city_address': partner.city,
                'postal_zone': partner.zip,
                # Not a geographic state/governorate code (Odoo's res.country.state has no such
                # concept for Oman) - Flick's live validator only accepts one of Oman's 4 named free
                # zones (SHRFZ/SEZAD/SLLFZ/AFZ) or "MO" for Mainland Oman. Odoo has no field recording
                # free-zone registration, so default every partner to "MO" - true for the vast
                # majority of businesses.
                'country_subdivision_code': "MO",
                'country_code': partner.country_id.code,
                'contact_name': partner.name,
                'contact_telephone': partner.phone,
                'contact_email': partner.email,
            }

        def _invoice_line(index, line):
            tax = line.tax_ids[:1]
            return {
                'id': str(index),
                'name': line.product_id.name or line.name,
                'description': line.name,
                'quantity': str(line.quantity),
                'uom': builder._get_uom_unece_code(line.product_uom_id),
                'unit_price': "%.2f" % line.price_unit,
                'base_quantity': "1",
                'line_extension_amount': "%.2f" % line.price_subtotal,
                'vat_category': builder._get_tax_category_code(customer, supplier, tax),
                'vat_percentage': "%.2f" % (tax.amount if tax else 0.0),
                'item_type': "GS",  # see class docstring: only one example value documented, no enum list
                'line_total_including_vat': "%.2f" % line.price_total,
            }

        now = datetime.now(timezone.utc)
        return {
            'uuid': document.l10n_om_edi_uuid,
            'document_identifier': move.name,
            'issue_date': move.invoice_date.isoformat() if move.invoice_date else None,
            'issue_time': now.strftime('%H:%M:%S'),
            'due_date': move.invoice_date_due.isoformat() if move.invoice_date_due else None,
            'document_type': '381' if move.move_type == 'out_refund' else '380',
            'document_currency': move.currency_id.name,
            'transaction_type_code': '0' * 20,
            # Their docs call this "sending_party", but the live validator only recognizes
            # "issuing_party" - using their documented name here gets the seller rejected as missing.
            'issuing_party': _party(supplier),
            'receiving_party': _party(customer),
            'invoice_lines': [_invoice_line(index, line) for index, line in enumerate(lines, start=1)],
            'invoice_totals': {
                'line_extension_amount': "%.2f" % move.amount_untaxed,
                'tax_exclusive_amount': "%.2f" % move.amount_untaxed,
                'tax_inclusive_amount': "%.2f" % move.amount_total,
                'payable_amount': "%.2f" % move.amount_total,
            },
        }

    def _handle_submit_response(self, response):
        """ Flick reports both transport-level failures (4xx/5xx) and business-validation failures
        (a "failed" status in an otherwise-200 JSON body) - handled here rather than via the shared
        `_handle_response()` so validation errors can be surfaced field-by-field instead of collapsing
        into a generic "could not process this request" message. """
        if response.status_code in (401, 403):
            raise UserError(_(
                "Authentication with Flick Network failed. Please check the API credentials configured "
                "in Settings > Accounting > Oman E-Invoicing."
            ))
        try:
            payload = response.json()
        except ValueError:
            raise UserError(_(
                "Flick Network returned an unexpected (non-JSON) response (%(status)s) while "
                "submitting this invoice:\n%(body)s",
                status=response.status_code, body=response.text[:2000],
            ))
        if payload.get('status') != 'success':
            # Errors can appear nested under "data" (documented) or at the top level (seen live).
            errors = (payload.get('data') or {}).get('errors') or payload.get('errors') or []
            if errors:
                details = '\n'.join('- %s' % self._format_flick_error(error) for error in errors)
                raise UserError(_(
                    "Flick Network rejected this invoice:\n%(details)s", details=details,
                ))
            message = payload.get('message') or (payload.get('data') or {}).get('message') or payload.get('error')
            raise UserError(_(
                "Flick Network rejected this invoice submission (%(status)s):\n%(body)s",
                status=response.status_code, body=message or response.text[:2000],
            ))
        # A real submission confirmed the tracking identifier is returned as `data.id`, not the
        # documented `data.document_id` - kept as a fallback in case a future API revision changes this.
        document_id = (payload.get('data') or {}).get('id') or (payload.get('data') or {}).get('document_id')
        if not document_id:
            raise UserError(_(
                "Flick Network accepted the submission but did not return a document_id to track it."
            ))
        return document_id

    @staticmethod
    def _format_flick_error(error):
        """ Format one entry of Flick's error list without assuming their documented key names
        ('field_name'/'error_message') are exactly what the live sandbox actually returns - try the
        documented names and a couple of plausible alternates first, falling back to the raw error
        object as JSON so nothing is ever hidden behind a generic "Unknown error". """
        if not isinstance(error, dict):
            return str(error)
        field = error.get('field_name') or error.get('field') or error.get('path')
        message = error.get('error_message') or error.get('message') or error.get('description')
        if field or message:
            return "%s: %s" % (field or '?', message or json.dumps(error))
        return json.dumps(error)

    def get_status(self, asp_reference):
        """ GET /v1/{participant_id}/documents/{document_id} - confirmed to reuse the same
        status/exchange_status/reporting_status envelope as the Submit Document response. """
        payload = self._request(
            'GET', f'/v1/{self.account_id}/documents/{asp_reference}',
            headers={'X-Flick-Auth-Key': self.api_key},
        )
        document = payload.get('data') or {}
        return {
            'processing': 'in_progress',
            'completed': 'accepted',
            'failed': 'rejected',
        }.get(document.get('status'), 'in_progress')

    def cancel(self, asp_reference, reason):
        """ Not implemented: Flick documents no cancel/void endpoint, only "Retry Document". """
        raise UserError(_(
            "No cancellation-specific endpoint was found among Flick Network's documented operations "
            "(only 'Retry Document') - Oman/Peppol e-invoicing generally corrects via credit notes "
            "rather than true cancellation, which this module already supports separately. Confirm "
            "with Flick directly whether any cancel/void operation exists before implementing this."
        ))
