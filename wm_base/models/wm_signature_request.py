#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import hashlib
import io
import logging
import uuid

from PIL import Image as PILImage
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.pdf import PdfFileReader, PdfFileWriter

_logger = logging.getLogger(__name__)


def _pdf_pages(reader):
    """Return the pages of a PDF reader across pypdf / PyPDF2 versions."""
    if hasattr(reader, 'pages'):
        return list(reader.pages)
    return [reader.getPage(i) for i in range(reader.getNumPages())]


class WmSignatureRequest(models.Model):
    """Tracks a digital signature workflow lifecycle from invitation through full completion."""
    _name = 'wm.signature.request'
    _description = 'Signature Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: self.env._('New'))
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    template_id = fields.Many2one('wm.signature.template', required=True, tracking=True)
    reference_doc = fields.Reference(
        selection='_selection_target_model',
        string='Linked Document',
        tracking=True,
        index=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'To Sign'),
        ('signed', 'Fully Signed'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True, copy=False)
    signer_ids = fields.One2many('wm.signature.request.signer', 'request_id', string='Signers', copy=True)
    item_value_ids = fields.One2many('wm.signature.request.item.value', 'request_id', string='Field Values')
    signed_document = fields.Binary(string='Signed Document (PDF)', attachment=True, readonly=True, copy=False)
    signed_document_filename = fields.Char(copy=False)
    signed_document_hash = fields.Char(
        string='Signed Document SHA-256', readonly=True, copy=False,
        help='SHA-256 of the signed PDF, recorded when the request was completed.')
    date_requested = fields.Datetime(default=fields.Datetime.now, readonly=True, copy=False)
    date_signed = fields.Datetime(string='Date Completed', readonly=True, copy=False)

    def action_verify_signed_document(self):
        """Return True when the stored signed PDF still matches its recorded hash."""
        self.ensure_one()
        if not (self.signed_document and self.signed_document_hash):
            return False
        return hashlib.sha256(base64.b64decode(self.signed_document)).hexdigest() == self.signed_document_hash

    @api.model
    def _selection_target_model(self):
        """
        Return the fixed list of signable target models (collection order,
        contract, batch inspection), limited to those installed.
        """
        candidates = [
            ('wm.collection.order', self.env._('Collection Order')),
            ('wm.partner.contract', self.env._('Contract')),
            ('wm.batch.inspection', self.env._('Waste Batch Inspection')),
        ]
        # Only offer models whose module is installed, otherwise the
        # Reference field raises KeyError on unknown models.
        return [(model, label) for model, label in candidates if model in self.env]

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to auto-generate a unique reference code for each
        signature request and check access to the linked document.
        """
        for vals in vals_list:
            if vals.get('name', self.env._('New')) == self.env._('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.signature.request') or self.env._('New')
            self._check_reference_doc_access(vals.get('reference_doc'))
        return super().create(vals_list)

    @api.model
    def _check_reference_doc_access(self, reference_doc):
        """
        A user may only start a signature request on a document they can
        modify. The signed PDF of the linked document is served to signers and
        completion writes back to it under sudo, so without this check any
        signature user could pull the PDF of an arbitrary order or contract.
        Superuser (sudo) flows have already done their own checks.
        """
        if not reference_doc or self.env.su:
            return
        if isinstance(reference_doc, str):
            model, _sep, res_id = reference_doc.partition(',')
        else:
            model, res_id = reference_doc._name, reference_doc.id
        if model not in self.env or not res_id:
            raise UserError(self.env._("The linked document is not valid."))
        record = self.env[model].browse(int(res_id)).exists()
        if not record:
            raise UserError(self.env._("The linked document no longer exists."))
        record.check_access('write')

    def _get_signer_url(self, signer_id):
        """
        Return the public portal signing URL for the given signer, built from
        the signer's access token.
        """
        self.ensure_one()
        if not signer_id:
            return ''
        signer = self.env['wm.signature.request.signer'].browse(signer_id)
        token = signer.access_token or ''
        return f"{self.get_base_url()}/wm_signature/sign/{token}"

    def action_view_reference_doc(self):
        """
        Open the source document (collection order, contract, or inspection)
        that triggered this signature request, providing quick navigation from
        the signature record.
        """
        self.ensure_one()
        if not self.reference_doc:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.reference_doc._name,
            'res_id': self.reference_doc.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_send(self):
        """
        Mark the request as sent, email each signer their portal signing link
        and log it in the chatter.
        """
        self.ensure_one()
        if self.state not in ('draft', 'sent'):
            raise UserError(self.env._("A signed or cancelled signature request cannot be sent."))
        if not self.signer_ids:
            raise UserError(self.env._("Please add at least one signer before sending the request."))

        self.write({'state': 'sent'})

        # Send emails to each signer
        mail_template = self.env.ref('wm_base.mail_template_signature_request', raise_if_not_found=False)
        if mail_template:
            for signer in self.signer_ids:
                # Send the email template specifically rendered for this signer
                mail_template.with_context(signer_id=signer.id).send_mail(
                    self.id,
                    force_send=True,
                    email_values={'email_to': signer.email}
                )

        # Log chatter message
        self.message_post(body=self.env._("Signature request sent to all signers."))

    def action_cancel(self):
        """
        Cancel the signature request (fully signed requests cannot be
        cancelled) and log it in the chatter.
        """
        if self.filtered(lambda r: r.state == 'signed'):
            raise UserError(self.env._("A fully signed request cannot be cancelled."))
        self.write({'state': 'cancel'})
        self.message_post(body=self.env._("Signature request cancelled."))

    def _check_request_completion(self):
        """
        Verify that all required signers have completed their signatures before
        the request is marked as fully signed, preventing partial-signature
        approval of regulated documents.
        """
        self.ensure_one()
        # Concurrent last signers: serialize on the request row and re-read, so
        # exactly one of them completes it (and only one certificate is made).
        self.env.cr.execute("SELECT id FROM wm_signature_request WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset(['state'])
        self.signer_ids.invalidate_recordset(['state'])
        # Only an open request can complete (a late signature on a draft or
        # cancelled request must not mark it, or its document, as signed)
        if self.state != 'sent':
            return
        # If all signers have signed, transition to fully signed state and generate PDF certificate
        if all(signer.state == 'signed' for signer in self.signer_ids):
            self.write({
                'state': 'signed',
                'date_signed': fields.Datetime.now()
            })
            self._generate_signed_certificate()
            self.message_post(body=self.env._("Document has been fully signed. Certificate of Completion generated."))

    def _render_reference_pdf(self):
        """ Render the PDF tied to the linked business document. """
        self.ensure_one()
        if not self.reference_doc:
            return False

        report_xmlid = False
        if self.reference_doc._name in ('wm.partner.contract', 'partner.contract'):
            report_xmlid = 'wm_contracts_billing.partner_contract_report'
        elif self.reference_doc._name == 'wm.collection.order':
            report_xmlid = 'wm_collection.collection_order_report'
        elif self.reference_doc._name == 'wm.batch.inspection':
            report_xmlid = 'wm_collection.action_report_batch_inspection'

        if not report_xmlid:
            return False

        try:
            pdf_content, _format = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                report_xmlid, [self.reference_doc.id]
            )
            return pdf_content or False
        except Exception as e:
            _logger.exception("wm_signature: _render_reference_pdf failed for %s id=%s: %s", report_xmlid, self.reference_doc.id, e)
            # Never fall back to a blank template: signers would sign (and a
            # certificate would be issued for) a document that is not the real one.
            raise UserError(self.env._(
                "The document to sign could not be generated. Please contact support "
                "before signing."))

    def _get_document_pdf(self):
        """ Retrieve the base PDF binary content for the signing page. """
        self.ensure_one()
        if self.state == 'signed' and self.signed_document:
            # A completed request always shows its frozen signed copy
            return base64.b64decode(self.signed_document)
        if (
            self.reference_doc
            and self.reference_doc._name == 'wm.collection.order'
            and getattr(self.reference_doc, 'collection_report_pdf', False)
        ):
            return base64.b64decode(self.reference_doc.collection_report_pdf)

        # For contracts and other reference docs, always try to render the live document PDF first
        if self.reference_doc:
            rendered = self._render_reference_pdf()
            if rendered:
                return rendered

        # Fall back to the template's stored document binary
        if self.template_id and self.template_id.document:
            return base64.b64decode(self.template_id.document)

        return False

    def _generate_signed_certificate(self):
        """
        Overlay the captured values on the base PDF, store the signed PDF with
        its SHA-256 hash for tamper verification, attach it to the linked
        document (or the request) and advance the linked document's signed
        state.
        """
        self.ensure_one()
        # 1. Load original PDF (dynamically generated contract PDF if contract linked, else template document)
        original_pdf_data = self._get_document_pdf()
        if not original_pdf_data:
            raise UserError(self.env._("No base PDF document found for this signature request."))
        # odoo.tools.pdf wraps whichever pypdf/PyPDF2 version Odoo runs on
        pdf_reader = PdfFileReader(io.BytesIO(original_pdf_data), strict=False)
        pdf_writer = PdfFileWriter()

        # 2. Iterate through each page
        for page_idx, page in enumerate(_pdf_pages(pdf_reader)):
            page_num = page_idx + 1

            # Get media box dimensions (points)
            mediabox = page.mediabox if hasattr(page, 'mediabox') else page.mediaBox
            page_width = float(mediabox.width if hasattr(mediabox, 'width') else mediabox.getWidth())
            page_height = float(mediabox.height if hasattr(mediabox, 'height') else mediabox.getHeight())

            # Find values filled for items on this page
            page_values = self.item_value_ids.filtered(lambda v: v.item_id.page == page_num)

            if page_values:
                # Create transparent PDF page using reportlab
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(page_width, page_height))
                has_drawn_items = False

                for val in page_values:
                    item = val.item_id
                    item_x = item.x
                    item_y = item.y
                    item_w = item.width
                    item_h = item.height

                    # If linked to a Contract, QWeb template (partner_contract_report_template.xml) already renders signature_image in HTML.
                    # Skip PDF overlay for signatures to prevent double rendering.
                    if self.reference_doc and self.reference_doc._name in ('wm.partner.contract', 'partner.contract'):
                        if item.type == 'signature':
                            continue
                        if item.type == 'date':
                            item_x = 8.0
                            item_y = 86.0
                            item_w = 30.0
                            item_h = 4.0

                    # Calculate coordinates in points
                    x_pts = (item_x / 100.0) * page_width
                    # PDF coordinate origin is bottom-left, browser coordinate origin is top-left
                    y_pts = page_height - (((item_y + item_h) / 100.0) * page_height)
                    w_pts = (item_w / 100.0) * page_width
                    h_pts = (item_h / 100.0) * page_height

                    if item.type == 'signature' and val.signature_image:
                        try:
                            img_data = base64.b64decode(val.signature_image)
                            img = PILImage.open(io.BytesIO(img_data))
                            temp_img_io = io.BytesIO()
                            img.save(temp_img_io, format='PNG')
                            temp_img_io.seek(0)
                            can.drawImage(ImageReader(temp_img_io), x_pts, y_pts, width=w_pts, height=h_pts, mask='auto')
                            has_drawn_items = True
                        except Exception as e:
                            _logger.warning("wm_signature: Failed to render signature image for request %s (signer %s): %s", self.id, val.signer_id.id, e)
                            can.setFont("Helvetica-Bold", 8)
                            can.drawString(x_pts + 4, y_pts + 8, f"Signed: {val.signer_id.partner_id.name}")
                            has_drawn_items = True
                    else:
                        text_str = val.value or ''
                        if item.type == 'name':
                            text_str = val.signer_id.partner_id.name
                        elif item.type == 'email':
                            text_str = val.signer_id.partner_id.email or ''
                        elif item.type == 'date':
                            text_str = val.value or fields.Date.today().strftime('%Y-%m-%d')

                        can.setFont("Helvetica", 8)
                        can.drawString(x_pts + 4, y_pts + 8, text_str)
                        has_drawn_items = True

                if has_drawn_items:
                    can.save()
                    packet.seek(0)

                    # Merge the transparent page onto the original page
                    overlay_pages = _pdf_pages(PdfFileReader(packet, strict=False))
                    if overlay_pages:
                        if hasattr(page, 'merge_page'):
                            page.merge_page(overlay_pages[0])
                        else:
                            page.mergePage(overlay_pages[0])

            if hasattr(pdf_writer, 'add_page'):
                pdf_writer.add_page(page)
            else:
                pdf_writer.addPage(page)

        # Write merged PDF to binary field
        output_stream = io.BytesIO()
        pdf_writer.write(output_stream)
        pdf_content = output_stream.getvalue()

        # Save signed document on the request
        filename = f"{self.template_id.name}_Signed_{self.name.replace('/', '_')}.pdf"
        self.write({
            'signed_document': base64.b64encode(pdf_content),
            'signed_document_filename': filename,
            'signed_document_hash': hashlib.sha256(pdf_content).hexdigest(),
        })

        # Create Odoo attachment
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self.reference_doc._name if self.reference_doc else self._name,
            'res_id': self.reference_doc.id if self.reference_doc else self.id,
        })

        # If linked to a Reference Document, update it
        if self.reference_doc:
            # Post log on the referenced document with attachment
            self.reference_doc.message_post(
                body=self.env._("The document signature request has been completed. Signed certificate attached."),
                attachment_ids=[attachment.id]
            )

            # Write to the collection order signature status
            if 'is_signed' in self.reference_doc._fields:
                self.reference_doc.sudo().write({'is_signed': True})

            # Move the document to 'signed' only from its pre-signature state;
            # never regress an ongoing/expired/cancelled contract or order.
            if self.reference_doc._name in ('wm.partner.contract', 'partner.contract'):
                if self.reference_doc.state in ('draft', 'sent'):
                    self.reference_doc.sudo().write({'state': 'signed'})
            elif self.reference_doc._name == 'wm.collection.order':
                if self.reference_doc.state == 'completed':
                    self.reference_doc.sudo().with_context(programmatic_state_change=True).write({'state': 'signed'})
            # If state is 'in_progress', we can transition it to 'completed'
            elif hasattr(self.reference_doc, 'state') and self.reference_doc.state == 'in_progress':
                self.reference_doc.sudo().write({
                    'state': 'completed',
                    'completed_date': fields.Datetime.now()
                })


class WmSignatureRequestSigner(models.Model):
    """Designated signer participant on a digital signature request with status and token."""
    _name = 'wm.signature.request.signer'
    _description = 'Signature Request Signer'

    request_id = fields.Many2one('wm.signature.request', string='Signature Request', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', required=True)
    role_id = fields.Many2one('wm.signature.role', required=True)
    # Own copy of the address (defaulted from the partner): editing it must
    # never overwrite the partner's email on res.partner.
    email = fields.Char(compute='_compute_email', store=True, readonly=False)
    access_token = fields.Char(required=True, default=lambda self: str(uuid.uuid4()), copy=False)
    state = fields.Selection([
        ('sent', 'To Sign'),
        ('signed', 'Signed')
    ], string='Status', default='sent', copy=False)
    signature_image = fields.Binary(compute='_compute_signature_image')
    # Set only by the signing flow (which runs as superuser), never by RPC writes.
    _SIGNING_PROTECTED_FIELDS = ('state', 'signed_date', 'ip_address', 'user_agent', 'access_token')
    signed_date = fields.Datetime(copy=False)
    ip_address = fields.Char(string='IP Address', copy=False)
    user_agent = fields.Char(copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            for vals in vals_list:
                if vals.get('state', 'sent') != 'sent' or vals.get('signed_date'):
                    raise AccessError(self.env._("A signer can only be marked as signed by the signing process."))
        return super().create(vals_list)

    def write(self, vals):
        """Only the signing flow (superuser) may record that someone signed.
        Request creators may edit a signer's name/email but never forge the
        signature evidence of other signers."""
        if not self.env.su and any(f in vals for f in self._SIGNING_PROTECTED_FIELDS):
            raise AccessError(self.env._("Signature status and evidence can only be set by the signing process."))
        return super().write(vals)

    @api.depends('partner_id')
    def _compute_email(self):
        """Default the signer email from the partner (only re-run when the
        partner changes, so manual edits are kept)."""
        for signer in self:
            signer.email = signer.partner_id.email or signer.email

    @api.depends('request_id.item_value_ids.signature_image')
    def _compute_signature_image(self):
        """
        Retrieve the first signature image captured by the signer from the
        linked signature line record, displaying it on the signature request
        form for visual confirmation.
        """
        for signer in self:
            val = self.env['wm.signature.request.item.value'].search([
                ('request_id', '=', signer.request_id.id),
                ('signer_id', '=', signer.id),
                ('signature_image', '!=', False)
            ], limit=1)
            signer.signature_image = val.signature_image if val else False

    def action_sign_signer(self):
        """
        Redirect to this signer's portal signing page, where they can draw or
        upload their signature.
        """
        self.ensure_one()
        url = f"/wm_signature/sign/{self.access_token}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

    _access_token_unique = models.Constraint(
        'unique(access_token)',
        'The access token must be unique!'
    )
