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
import base64
import logging
import uuid

from lxml import etree

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.account.tools import dict_to_xml

_logger = logging.getLogger(__name__)


class L10nOmEdiDocument(models.Model):
    """ Tracks the submission of one invoice/credit note to Oman's e-invoicing 5-corner Peppol
    network through the company's configured Accredited Service Provider (ASP).

    Unlike a clearance model (e.g. Saudi ZATCA), Oman's Corner 5 (the Oman Tax Authority) only
    receives an acknowledgement of a Tax Data Document (TDD) report - it does not validate/clear the
    invoice itself. `l10n_om_edi_state` reflects that: 'accepted' means the ASP/OTA acknowledged
    receipt of the report, not that the invoice was "approved".
    """
    _name = 'l10n.om.edi.document'
    _inherit = ['mail.thread', 'sequence.mixin']
    _description = "Oman E-Invoicing Document"
    _order = 'l10n_om_edi_issuance_date desc, id desc'
    _check_company_auto = True
    _sequence_date_field = 'l10n_om_edi_issuance_date'

    name = fields.Char(compute='_compute_name', store=True, copy=False, index='trigram')
    company_id = fields.Many2one(comodel_name='res.company', required=True, readonly=True,
                                  default=lambda self: self.env.company)
    move_id = fields.Many2one(comodel_name='account.move', string="Invoice/Credit Note", required=True,
                               readonly=True, index=True, check_company=True)
    l10n_om_edi_issuance_date = fields.Date(related='move_id.invoice_date', store=True, readonly=True)
    l10n_om_edi_uuid = fields.Char(
        string="UUID",
        readonly=True,
        copy=False,
        help="Supplier-generated UUID identifying this document, printed on the QR code. "
             "Generated locally so it is available even before the ASP acknowledges the submission.",
    )

    l10n_om_edi_state = fields.Selection(
        string="Submission State",
        selection=[
            ('to_send', "To Send"),
            ('in_progress', "Submission In Progress"),
            ('accepted', "Acknowledged"),
            ('rejected', "Rejected"),
            ('error', "Error"),
            ('cancelled', "Cancelled"),
        ],
        default='to_send',
        copy=False,
        readonly=True,
        tracking=True,
        help="'Acknowledged' means the ASP/Oman Tax Authority has acknowledged receipt of the Tax Data "
             "Document report - Oman's model has no invoice clearance/validation step.",
    )
    asp_reference = fields.Char(string="ASP Reference", copy=False, readonly=True,
                                 help="Reference assigned by the Accredited Service Provider to this submission.")
    error_message = fields.Text(string="Error Message", copy=False, readonly=True)
    retry_count = fields.Integer(default=0, copy=False, readonly=True)

    invoice_xml = fields.Binary(string="Invoice XML", copy=False, readonly=True, attachment=True,
                                 export_string_translation=False)
    invoice_xml_fname = fields.Char(compute='_compute_invoice_xml_fname')
    tdd_xml = fields.Binary(string="Tax Data Document XML", copy=False, readonly=True, attachment=True,
                             export_string_translation=False,
                             help="The separate Corner-5 report sent to the Oman Tax Authority "
                                  "(urn:peppol:taxdata:om-1), distinct from the invoice XML itself.")
    tdd_xml_fname = fields.Char(compute='_compute_tdd_xml_fname')

    qr_code = fields.Image(string="QR Code", compute='_compute_qr_code')

    @api.depends('l10n_om_edi_issuance_date')
    def _compute_name(self):
        """ Assign the next OMEDI/YYYY/NNNNN sequence number once the issuance date is known. """
        for document in self.sorted(key=lambda d: (d.l10n_om_edi_issuance_date, d._origin.id)):
            document_has_name = document.name and document.name != '/'
            if document_has_name:
                if not document._sequence_matches_date():
                    document.name = False
                    continue
            if document.l10n_om_edi_issuance_date and not document_has_name:
                document._set_next_sequence()
        self.filtered(lambda d: not d.name).name = '/'

    def _compute_invoice_xml_fname(self):
        """ Derive the invoice XML attachment's filename from the invoice number. """
        for document in self:
            document.invoice_xml_fname = document.move_id.name and f"{document.move_id.name.replace('/', '_')}_pint_om.xml"

    def _compute_tdd_xml_fname(self):
        """ Derive the Tax Data Document XML attachment's filename from the invoice number. """
        for document in self:
            document.tdd_xml_fname = document.move_id.name and f"{document.move_id.name.replace('/', '_')}_tdd.xml"

    def _compute_qr_code(self):
        """ Generate the QR code image for any out_invoice document, or False otherwise. """
        for document in self:
            document.qr_code = document._generate_qr_code() if document.move_id.move_type == 'out_invoice' else False

    def _get_starting_sequence(self):
        """ Return the first sequence value for a given issuance year, e.g. 'OMEDI/2026/00000'. """
        self.ensure_one()
        return "OMEDI/%04d/00000" % (self.l10n_om_edi_issuance_date or fields.Date.context_today(self)).year

    def _get_last_sequence_domain(self, relaxed=False):
        """ Returns the SQL WHERE statement to use when fetching the latest record with the same
        sequence, and its params. Required override: the sequence.mixin base returns an empty ("",
        {}) domain, which is not valid SQL on its own. """
        self.ensure_one()
        if not self.l10n_om_edi_issuance_date:
            return "WHERE FALSE", {}
        where_string = "WHERE name != '/'"
        param = {}

        if not relaxed:
            domain = [('id', '!=', self.id or self._origin.id), ('name', 'not in', ('/', '', False))]
            reference_name = self.sudo().search(domain + [('l10n_om_edi_issuance_date', '<=', self.l10n_om_edi_issuance_date)], limit=1).name
            if not reference_name:
                reference_name = self.sudo().search(domain, order='l10n_om_edi_issuance_date asc', limit=1).name
            sequence_number_reset = self._deduce_sequence_number_reset(reference_name)
            date_start, date_end, *_ = self._get_sequence_date_range(sequence_number_reset)
            where_string += " AND l10n_om_edi_issuance_date BETWEEN %(date_start)s AND %(date_end)s"
            param['date_start'] = date_start
            param['date_end'] = date_end

        return where_string, param

    @api.model_create_multi
    def create(self, vals_list):
        """ Generate the supplier-side UUID locally at creation time, not deferred to submission. """
        for vals in vals_list:
            vals.setdefault('l10n_om_edi_uuid', str(uuid.uuid4()))
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # XML generation
    # -------------------------------------------------------------------------

    def _generate_invoice_xml(self):
        """ Generate the PINT OM Invoice/CreditNote XML for `self.move_id` (Corners 1-4). """
        self.ensure_one()
        builder = self.env['account.edi.xml.pint_om']
        xml_content, errors = builder._export_invoice(self.move_id)
        if errors:
            raise UserError(_("Could not generate the PINT OM invoice XML:\n%s", '\n'.join(errors)))
        self.invoice_xml = base64.b64encode(xml_content)
        return xml_content

    def _generate_tdd_xml(self):
        """ Generate the Tax Data Document (TDD) XML sent to the Oman Tax Authority (Corner 5).

        NOTE: the OTA's official TDD XSD/schematron (urn:peppol:taxdata:om-1) was not publicly
        available at the time this was written - this is a best-effort placeholder covering only the
        summary fields in the regulatory brief, to revisit once the official schema is published.
        """
        self.ensure_one()
        move = self.move_id
        supplier = move.company_id.partner_id.commercial_partner_id
        customer = move.partner_id.commercial_partner_id
        node = {
            '_tag': 'pxs:TaxDataDocument',
            'pxs:UUID': {'_text': self.l10n_om_edi_uuid},
            'pxs:IssueDate': {'_text': move.invoice_date and move.invoice_date.isoformat()},
            'pxs:DocumentTypeCode': {'_text': '381' if move.move_type == 'out_refund' else '380'},
            'pxs:InvoiceReference': {'_text': move.name},
            'pxs:Supplier': {
                'pxs:VATIN': {'_text': supplier.vat},
            },
            'pxs:Customer': {
                'pxs:VATIN': {'_text': customer.vat},
            },
            'pxs:TaxTotal': {'_text': str(move.amount_tax)},
            'pxs:LegalMonetaryTotal': {'_text': str(move.amount_total)},
        }
        xml_element = dict_to_xml(node, nsmap={'pxs': 'urn:peppol:taxdata:om-1'})
        xml_content = etree.tostring(xml_element, xml_declaration=True, encoding='UTF-8')
        self.tdd_xml = base64.b64encode(xml_content)
        return xml_content

    def _generate_qr_code(self):
        """ Generate the QR code (seller name, VATIN, timestamp, total incl. VAT, VAT amount,
        supplier-generated UUID), TLV-packed like l10n_sa_edi's but without ZATCA's hash/signature.

        ASSUMPTION: the OTA's exact QR spec (TLV vs. URL vs. JSON) wasn't publicly available at the
        time this was written - kept isolated here so it's cheap to change once the spec is public.
        """
        self.ensure_one()
        move = self.move_id
        if not (move.invoice_date and self.l10n_om_edi_uuid):
            return False

        def _encode(tag, value):
            value_bytes = str(value).encode()
            return tag.to_bytes(length=1, byteorder='big') + len(value_bytes).to_bytes(length=1, byteorder='big') + value_bytes

        seller_name = move.company_id.display_name
        seller_vat = move.company_id.vat or ''
        timestamp = move.invoice_date.isoformat()
        payload = (
            _encode(1, seller_name)
            + _encode(2, seller_vat)
            + _encode(3, timestamp)
            + _encode(4, f"{move.amount_total:.2f}")
            + _encode(5, f"{move.amount_tax:.2f}")
            + _encode(6, self.l10n_om_edi_uuid)
        )

        qr_code = self.env['ir.actions.report'].barcode(
            barcode_type='QR',
            value=base64.b64encode(payload).decode(),
            width=128,
            height=128,
            humanreadable=1,
        )
        return base64.b64encode(qr_code)

    # -------------------------------------------------------------------------
    # Submission
    # -------------------------------------------------------------------------

    def action_retry_submission(self):
        """ Public wrapper around `_action_submit`, callable from view buttons. """
        self._action_submit()

    def _action_submit(self):
        """ Submit the invoice + TDD XML to the company's configured ASP. """
        for document in self:
            try:
                invoice_xml = document._generate_invoice_xml()
                tdd_xml = document._generate_tdd_xml()
                connector = document.company_id._l10n_om_edi_get_connector()
                reference = connector.submit_invoice(invoice_xml, tdd_xml, document)
            except UserError as e:
                document.l10n_om_edi_state = 'error'
                document.error_message = str(e)
                document.retry_count += 1
                continue

            document.write({
                'l10n_om_edi_state': 'in_progress',
                'asp_reference': reference,
                'error_message': False,
            })

    def _cron_poll_submission_status(self):
        """ Poll the ASP for documents still 'in_progress'. Degrades to a no-op for companies without
        a configured connector, so this cron is safe to run even before an ASP is wired in. """
        documents = self.search([('l10n_om_edi_state', '=', 'in_progress'), ('asp_reference', '!=', False)])
        for company, company_documents in documents.grouped('company_id').items():
            if not company.l10n_om_edi_asp_provider:
                continue
            connector = company._l10n_om_edi_get_connector()
            for document in company_documents:
                try:
                    state = connector.get_status(document.asp_reference)
                except UserError as e:
                    _logger.warning("Error polling Oman e-invoicing status for %s: %s", document.name, e)
                    continue
                if state in dict(self._fields['l10n_om_edi_state'].selection):
                    document.l10n_om_edi_state = state
