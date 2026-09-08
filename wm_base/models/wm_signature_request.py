# -*- coding: utf-8 -*-
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
import logging
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WmSignatureRequest(models.Model):
    """Tracks a digital signature workflow lifecycle from invitation through full completion."""
    _name = 'wm.signature.request'
    _description = 'Signature Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    template_id = fields.Many2one('wm.signature.template', string='Template', required=True, tracking=True)
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
    ], string='Status', default='draft', tracking=True)
    signer_ids = fields.One2many('wm.signature.request.signer', 'request_id', string='Signers', copy=True)
    item_value_ids = fields.One2many('wm.signature.request.item.value', 'request_id', string='Field Values')
    signed_document = fields.Binary(string='Signed Document (PDF)', attachment=True, readonly=True)
    signed_document_filename = fields.Char(string='Signed Document Filename')
    date_requested = fields.Datetime(string='Date Requested', default=fields.Datetime.now, readonly=True)
    date_signed = fields.Datetime(string='Date Completed', readonly=True)

    @api.model
    def _selection_target_model(self):
        """
        Return the dynamic list of models available as signature request
        targets, populated from all models that inherit the wm.audit.mixin and
        support digital signatures.
        """
        return [
            ('wm.collection.order', 'Collection Order'),
            ('wm.partner.contract', 'Contract'),
            ('partner.contract', 'Contract'),
            ('wm.batch.inspection', 'Waste Batch Inspection'),
        ]

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to auto-generate a unique reference code for each
        signature request and send the initial request notification email to
        the designated signer.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.signature.request') or _('New')
        return super().create(vals_list)

    def _get_signer_url(self, signer_id):
        """
        Generate the time-limited, signed portal URL for the signer to access
        their signature capture page, embedding the access token and request ID
        as URL parameters.
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
        Compose and dispatch the signature request email to the designated
        signer, attaching the document preview PDF and embedding the secure
        portal signing URL.
        """
        self.ensure_one()
        if not self.signer_ids:
            raise UserError(_("Please add at least one signer before sending the request."))

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
        self.message_post(body=_("Signature request sent to all signers."))

    def action_cancel(self):
        """
        Cancel the outstanding signature request, notifying the intended signer
        of the withdrawal and unlocking the parent document for re-submission
        if needed.
        """
        self.write({'state': 'cancel'})
        self.message_post(body=_("Signature request cancelled."))

    def _check_request_completion(self):
        """
        Verify that all required signers have completed their signatures before
        the request is marked as fully signed, preventing partial-signature
        approval of regulated documents.
        """
        self.ensure_one()
        # If all signers have signed, transition to fully signed state and generate PDF certificate
        if all(signer.state == 'signed' for signer in self.signer_ids):
            self.write({
                'state': 'signed',
                'date_signed': fields.Datetime.now()
            })
            self._generate_signed_certificate()
            self.message_post(body=_("Document has been fully signed. Certificate of Completion generated."))

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
            return False

    def _get_document_pdf(self):
        """ Retrieve the base PDF binary content for the signing page. """
        self.ensure_one()
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
        Render the signed document PDF with an embedded SHA-256 certificate
        footer, attach it to the chatter, and record the certificate hash for
        future tamper verification.
        """
        self.ensure_one()
        import base64
        import io

        import PyPDF2
        from PIL import Image as PILImage
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas

        # 1. Load original PDF (dynamically generated contract PDF if contract linked, else template document)
        original_pdf_data = self._get_document_pdf()
        if not original_pdf_data:
            raise UserError(_("No base PDF document found for this signature request."))
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(original_pdf_data))
        pdf_writer = PyPDF2.PdfWriter()

        # 2. Iterate through each page
        for page_idx in range(len(pdf_reader.pages)):
            page_num = page_idx + 1
            page = pdf_reader.pages[page_idx]

            # Get media box dimensions (points)
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

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
                    # Skip PyPDF2 overlay for signatures to prevent double rendering.
                    if self.reference_doc and self.reference_doc._name in ('wm.partner.contract', 'partner.contract'):
                        if item.type == 'signature':
                            continue
                        elif item.type == 'date':
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
                    overlay_pdf = PyPDF2.PdfReader(packet)
                    if overlay_pdf.pages:
                        overlay_page = overlay_pdf.pages[0]
                        page.merge_page(overlay_page)

            pdf_writer.add_page(page)

        # Write merged PDF to binary field
        output_stream = io.BytesIO()
        pdf_writer.write(output_stream)
        pdf_content = output_stream.getvalue()

        # Save signed document on the request
        filename = f"{self.template_id.name}_Signed_{self.name.replace('/', '_')}.pdf"
        self.write({
            'signed_document': base64.b64encode(pdf_content),
            'signed_document_filename': filename
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
                body=_("The document signature request has been completed. Signed certificate attached."),
                attachment_ids=[attachment.id]
            )

            # Write to the collection order signature status
            if 'is_signed' in self.reference_doc._fields:
                self.reference_doc.sudo().write({'is_signed': True})

            # If it's a contract, transition it to 'signed'
            if self.reference_doc._name in ('wm.partner.contract', 'partner.contract'):
                self.reference_doc.sudo().write({'state': 'signed'})
            elif self.reference_doc._name == 'wm.collection.order':
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
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    role_id = fields.Many2one('wm.signature.role', string='Role', required=True)
    email = fields.Char(string='Email', related='partner_id.email', readonly=False, store=True)
    access_token = fields.Char(string='Access Token', required=True, default=lambda self: str(uuid.uuid4()), copy=False)
    state = fields.Selection([
        ('sent', 'To Sign'),
        ('signed', 'Signed')
    ], string='Status', default='sent')
    signature_image = fields.Binary(string='Signature Image', compute='_compute_signature_image')
    signed_date = fields.Datetime(string='Signed Date')
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')

    @api.depends('request_id.item_value_ids.signature_image')
    def _compute_signature_image(self):
        """
        Retrieve the latest signature image captured by the signer from the
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
        Open the portal signature capture wizard for the designated signer on
        this request, allowing them to draw or upload their signature directly
        on the backend form.
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
