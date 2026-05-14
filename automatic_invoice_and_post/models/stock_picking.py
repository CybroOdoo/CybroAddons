# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anjali VP @cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models
import base64

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """Validate delivery and optionally create, post, and email the invoice."""

        res = super().button_validate()

        auto_validate_invoice = self.env['ir.config_parameter'].sudo().get_param(
            'automatic_invoice_and_post.is_create_invoice_delivery_validate')
        auto_send_invoice = self.env['ir.config_parameter'].sudo().get_param(
            'automatic_invoice_and_post.is_auto_send_invoice')

        done_pickings = self.filtered(
            lambda p: p.state == 'done' and p.picking_type_code == 'outgoing' and p.sale_id
        )
        if not done_pickings:
            return res

        if auto_validate_invoice or auto_send_invoice:
            if any(rec.product_id.invoice_policy == 'delivery' for rec in
                   self.move_ids) or not self.sale_id.invoice_ids:
                invoice_created = self.sale_id._create_invoices(
                    self.sale_id) if self.sale_id else False
                if invoice_created:
                    invoice_created.action_post()

                    if auto_send_invoice and invoice_created.partner_id.email:
                        self._send_invoice_email(invoice_created)

        return res

    def _send_invoice_email(self, invoice):
        """Send invoice with PDF attachment via message_post"""
        try:
            report = self.env.ref('account.account_invoices')
            pdf_content, _ = report._render_qweb_pdf(report.id, res_ids=invoice.ids)
            pdf_base64 = base64.b64encode(pdf_content)

            if invoice.name and invoice.name != '/':
                file_name = invoice.name.replace('/', '_')
            else:
                file_name = f"Draft_Invoice_{invoice.invoice_origin or invoice.id}"

            attachment = self.env['ir.attachment'].create({
                'name': f"{file_name}.pdf",
                'type': 'binary',
                'datas': pdf_base64,
                'res_model': 'account.move',
                'res_id': invoice.id,
                'mimetype': 'application/pdf',
            })

            template = self.env.ref('account.email_template_edi_invoice')

            body_html = template._render_field('body_html', invoice.ids)[invoice.id]

            if invoice.state == 'draft':
                subject = f"{invoice.company_id.name} Invoice (Draft) - Ref {invoice.invoice_origin or ''}"
            else:
                subject = template._render_field('subject', invoice.ids)[invoice.id]

            invoice.message_post(
                body=body_html,
                subject=subject,
                message_type='email',
                partner_ids=[invoice.partner_id.id],
                attachment_ids=[attachment.id],
                subtype_xmlid='mail.mt_comment',
            )

            invoice.is_move_sent = True

        except Exception:
            pass
