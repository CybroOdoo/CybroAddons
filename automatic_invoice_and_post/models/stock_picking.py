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
#############################################################################
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    """Create, post and optionally email the invoice of the related sale
    order when a delivery is validated."""
    _inherit = 'stock.picking'

    def button_validate(self):
        """Validate the picking, then invoice the done deliveries according
        to the module settings."""
        res = super().button_validate()

        # If Odoo returned a wizard action (e.g. backorder confirmation),
        # the picking isn't actually validated yet — bail out and let the
        # user resolve it first.
        if isinstance(res, dict):
            return res

        param = self.env['ir.config_parameter'].sudo()
        auto_post_invoice = param.get_bool(
            'automatic_invoice_and_post.is_create_invoice_delivery_validate')
        if not auto_post_invoice:
            return res
        auto_send_invoice = param.get_bool(
            'automatic_invoice_and_post.is_auto_send_invoice')

        # Only the final delivery to the customer triggers invoicing, not
        # the pick/pack steps of a multi-step route.
        deliveries = self.filtered(
            lambda p: p.state == 'done' and p.picking_type_code == 'outgoing')
        for picking in deliveries:
            # The user validating a delivery may have no accounting rights.
            sale_order = picking.sudo().sale_id
            if not sale_order or sale_order.invoice_status != 'to invoice':
                continue
            invoices = sale_order._create_invoices()
            invoices.action_post()
            if auto_send_invoice:
                for invoice in invoices.filtered('partner_id.email'):
                    self._send_invoice_email(invoice)
        return res

    def _send_invoice_email(self, invoice):
        """Send the invoice with its PDF attachment via message_post.

        A failure is logged and rolled back so that it never blocks the
        delivery validation."""
        try:
            with self.env.cr.savepoint():
                report = invoice.env.ref('account.account_invoices')
                pdf_content, _ = report._render_qweb_pdf(
                    report.id, res_ids=invoice.ids)

                if invoice.name and invoice.name != '/':
                    file_name = invoice.name.replace('/', '_')
                else:
                    file_name = (f"Draft_Invoice_"
                                 f"{invoice.invoice_origin or invoice.id}")

                attachment = invoice.env['ir.attachment'].create({
                    'name': f"{file_name}.pdf",
                    'type': 'binary',
                    'raw': pdf_content,
                    'res_model': 'account.move',
                    'res_id': invoice.id,
                    'mimetype': 'application/pdf',
                })

                template = invoice.env.ref(
                    'account.email_template_edi_invoice')

                body_html = template._render_field(
                    'body_html', invoice.ids)[invoice.id]

                if invoice.state == 'draft':
                    subject = (f"{invoice.company_id.name} Invoice (Draft) - "
                               f"Ref {invoice.invoice_origin or ''}")
                else:
                    subject = template._render_field(
                        'subject', invoice.ids)[invoice.id]

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
            _logger.exception("Could not send invoice %s by email.",
                              invoice.display_name)
