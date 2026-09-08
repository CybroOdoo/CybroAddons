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
import logging
import urllib.parse

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class WmSignatureTemplate(models.Model):
    """Reusable digital signature document template with configurable visual field overlays."""
    _name = 'wm.signature.template'
    _description = 'Signature Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Template Name', required=True, tracking=True)
    document = fields.Binary(string='Document Template (PDF)', attachment=True, required=False)
    document_filename = fields.Char(string='Document Filename')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True, tracking=True)
    role_ids = fields.Many2many('wm.signature.role', string='Signer Roles', required=True,
                                help='Roles required to sign documents using this template.')
    item_ids = fields.One2many('wm.signature.item', 'template_id', string='Fields')

    def action_design_template(self):
        """
        Open the signature template visual designer, allowing administrators to
        position signature fields and date stamps on the PDF
        template layout.
        """
        self.ensure_one()
        # 0. Ensure at least one signer role is defined
        if not self.role_ids:
            default_role = self.env['wm.signature.role'].sudo().search([], limit=1)
            if not default_role:
                default_role = self.env['wm.signature.role'].sudo().create({'name': 'Signatory'})
            self.sudo().write({'role_ids': [(4, default_role.id)]})

        if not self.document:
            # 1. Check if there is a linked collection order referencing this template
            if 'wm.collection.order' in self.env:
                order = self.env['wm.collection.order'].sudo().search([('signature_template_id', '=', self.id)], limit=1)
                if order:
                    report = self.env.ref('wm_collection.collection_order_report', raise_if_not_found=False)
                    if report:
                        try:
                            pdf_content, _format = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                                'wm_collection.collection_order_report', [order.id]
                            )
                            if pdf_content:
                                import base64
                                self.sudo().write({
                                    'document': base64.b64encode(pdf_content),
                                    'document_filename': f"Collection_Order_{order.name}.pdf"
                                })
                        except Exception as e:
                            _logger.warning("Failed to render collection order report PDF for template %s: %s", self.id, e)

            # 2. If still no document, generate default PDF template
            if not self.document:
                pdf_binary = self._generate_default_pdf_document()
                if pdf_binary:
                    self.sudo().write({
                        'document': pdf_binary,
                        'document_filename': f"{self.name or 'Document'}.pdf"
                    })

        back_url = f"/web#id={self.id}&model={self._name}&view_type=form"
        encoded_back_url = urllib.parse.quote(back_url)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/wm_signature/template/edit/{self.id}?back_url={encoded_back_url}',
            'target': 'self',
        }

    def _generate_default_pdf_document(self):
        """
        Render the signature template's base QWeb report to a PDF binary,
        creating the default blank document that signers will receive when a
        signature request is dispatched.
        """
        import base64
        import io
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFillColorRGB(0.12, 0.14, 0.21)
            can.setFont("Helvetica-Bold", 20)
            can.drawString(50, 720, (self.name or "SIGNATURE TEMPLATE").upper())
            can.setStrokeColorRGB(0.8, 0.8, 0.8)
            can.line(50, 705, 550, 705)
            can.setFillColorRGB(0.3, 0.3, 0.3)
            can.setFont("Helvetica", 10)
            can.drawString(50, 680, "Electronic Signature Verification Document")
            y = 630
            paragraphs = [
                f"Document Reference: {self.name or 'N/A'}",
                "Description: " + (self.description or "Standard company authorization and signature verification document."),
                "",
                "1. TERMS AND CONDITIONS:",
                "   The signatory hereby confirms the accuracy of all details recorded within this document.",
                "   All operations, materials, and services detailed herein have been performed according to standard procedures.",
                "",
                "2. AUTHORIZATION & SIGN-OFF:",
                "   By placing an electronic signature below, the undersigned acknowledges full receipt and verification."
            ]

            for p in paragraphs:
                if p.startswith("1.") or p.startswith("2."):
                    can.setFont("Helvetica-Bold", 11)
                    can.setFillColorRGB(0.12, 0.14, 0.21)
                else:
                    can.setFont("Helvetica", 10)
                    can.setFillColorRGB(0.2, 0.2, 0.2)
                can.drawString(50, y, p)
                y -= 22
            y -= 40
            can.setFont("Helvetica-Bold", 11)
            can.drawString(50, y, "Authorized Signatures:")
            y -= 40
            can.setFont("Helvetica", 10)
            can.drawString(50, y, "Signature:")
            can.line(120, y - 2, 320, y - 2)
            can.drawString(350, y, "Date:")
            can.line(390, y - 2, 530, y - 2)
            can.save()
            packet.seek(0)
            return base64.b64encode(packet.getvalue())
        except Exception as e:
            _logger.warning("Failed to generate default PDF document for signature template %s: %s", self.id, e)
            return False

    @api.model
    def create_from_pdf(self, name, doc_base64, filename):
        """
        Create a new signature template record by importing an existing PDF
        binary, extracting page dimensions and storing the PDF as the base
        document for field placement.
        """
        role = self.env['wm.signature.role'].search([], limit=1)
        if not role:
            role = self.env['wm.signature.role'].sudo().create({'name': 'Signer'})

        template = self.create({
            'name': name or filename or 'Uploaded Document',
            'document': doc_base64,
            'document_filename': filename or 'document.pdf',
            'role_ids': [(6, 0, [role.id])],
        })
        return template.id

    @api.model
    def create_sample_template(self):
        """
        Generate a pre-populated sample signature template with common waste
        management document placeholders, helping administrators set up new
        environments quickly.
        """
        import base64
        import io

        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        role = self.env['wm.signature.role'].search([], limit=1)
        if not role:
            role = self.env['wm.signature.role'].sudo().create({'name': 'Signer'})

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        can.setFillColorRGB(0.1, 0.1, 0.4)
        can.setFont("Helvetica-Bold", 24)
        can.drawString(50, 700, "SAMPLE SERVICE CONTRACT")

        can.setStrokeColorRGB(0.7, 0.7, 0.7)
        can.line(50, 680, 550, 680)

        can.setFillColorRGB(0, 0, 0)
        can.setFont("Helvetica-Oblique", 11)
        can.drawString(50, 650, "This is a sample document generated automatically for demonstration purposes.")

        can.setFont("Helvetica", 10)
        y = 600
        paragraphs = [
            "1. AGREEMENT: The parties agree to perform the services detailed in the scope of work.",
            "2. TERM: This agreement shall begin on the date of signature and continue until services are complete.",
            "3. PAYMENT: Payment shall be rendered upon successful completion and verification of the services.",
            "4. LIABILITY: Neither party shall be liable for indirect, incidental, or consequential damages.",
            "5. CONFIDENTIALITY: Both parties agree to maintain the strict confidentiality of all proprietary data.",
            "6. ENTIRE AGREEMENT: This document constitutes the entire agreement between the customer and the provider."
        ]
        for p in paragraphs:
            can.drawString(50, y, p)
            y -= 25

        y -= 40
        can.setFont("Helvetica-Bold", 12)
        can.drawString(50, y, "Signatures:")

        y -= 50
        can.setFont("Helvetica", 10)
        can.drawString(50, y, "Customer Signature:")
        can.line(180, y - 2, 350, y - 2)

        can.drawString(380, y, "Date:")
        can.line(410, y - 2, 530, y - 2)

        can.save()
        packet.seek(0)
        pdf_data = packet.getvalue()

        template = self.create({
            'name': 'Sample Contract.pdf',
            'document': base64.b64encode(pdf_data),
            'document_filename': 'Sample_Contract.pdf',
            'role_ids': [(6, 0, [role.id])],
        })
        return template.id
