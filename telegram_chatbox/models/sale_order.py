# -*- coding: utf-8 -*-
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
from markupsafe import Markup, escape
from odoo import Command, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    """Extension of sale.order to support sending Telegram messages."""
    _inherit = "sale.order"
    _description = 'Sales Order'

    def send_telegram_message(self, text, telegram_template_id, bot=None, attachment_ids=None):
        """
            Send a Telegram message to the customer associated with the current
            Sale Order.

            This method renders the provided message using the specified Telegram
            template, validates the customer's Telegram settings, creates an outgoing
            Telegram message record, sends the message through the configured bot,
            and logs the communication in the Sale Order chatter.
        """
        self.ensure_one()
        
        converted_message = text
        if telegram_template_id:
            converted_message = telegram_template_id.render_template(text, record=self)
            
        if not self.partner_id.telegram_opt_in:
            raise ValidationError(
                _("Telegram messaging is disabled for this customer."))
        if not self.partner_id.telegram_chat_id:
            raise ValidationError(
                _("Telegram Chat ID is missing. Please link the partner with Telegram."))

        bot = (bot or self.partner_id.telegram_bot_id).sudo()
        if not bot:
            raise ValidationError(
                _("No Telegram Bot configured. Please set a default bot on the partner."))

        msg = self.env['telegram.message'].create({
            'direction': 'outgoing',
            'chat_id': self.partner_id.telegram_chat_id,
            'partner_id': self.partner_id.id,
            'telegram_template_id': telegram_template_id.id if telegram_template_id else False,
            'bot_id': bot.id,
            'res_model': 'sale.order',
            'res_id': self.id,
            'message_text': converted_message,
            'attachment_ids': [Command.set(attachment_ids)] if attachment_ids else False,
            'state': 'new',
        })

        msg.send_via_bot(converted_message, bot=bot)

        self.message_post(
            body=Markup("<b>Telegram Sent:</b><br/>%s") % escape(converted_message).replace('\n', Markup('<br/>')),
            attachment_ids=attachment_ids if attachment_ids else []
        )
        return True

    def action_send_telegram(self):
        """
        Open the Telegram message wizard for the current Sale Order and
        automatically attach the Sale Order PDF if available.

        This method checks for an existing PDF attachment linked to the Sale
        Order. If no suitable attachment is found, it generates a PDF version
        of the Sale Order report, creates an attachment, and preloads it into
        the Telegram message wizard.
        """
        self.ensure_one()
        
        report = self.env.ref('sale.action_report_saleorder', raise_if_not_found=False)
        pdf_attachment_id = False

        if report:
            pdf_content = None
            try:
                pdf_content, report_type = self.env['ir.actions.report']._render_qweb_pdf('sale.action_report_saleorder', self.ids)
            except Exception as e:
                _logger.warning("Standard Sale Order PDF Generation failed: %s", e)
                try:
                    html_rendered = self.env['ir.actions.report']._render_qweb_html('sale.action_report_saleorder', self.ids)[0]
                    pdf_content = self.env['ir.actions.report']._run_wkhtmltopdf([html_rendered])
                except Exception as fallback_e:
                    _logger.warning("Fallback Sale Order PDF rendering failed: %s", fallback_e)

            if pdf_content:
                attachment_name = (self.name or str(self.id)).replace('/', '_')
                attachment = self.env['ir.attachment'].create({
                    'name': f"{attachment_name}.pdf",
                    'type': 'binary',
                    'raw': pdf_content,
                    'res_model': 'sale.order',
                    'res_id': self.id,
                    'mimetype': 'application/pdf'
                })
                pdf_attachment_id = attachment.id

        if not pdf_attachment_id:
            existing_attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', self.id),
                ('name', 'like', f"{self.name}%"),
                ('mimetype', '=', 'application/pdf')
            ], order="id desc", limit=1)
            if existing_attachment:
                pdf_attachment_id = existing_attachment.id

        ctx = {
            'default_partner_id': self.partner_id.id,
            'default_sale_order_id': self.id,
        }
        if pdf_attachment_id:
            ctx['default_attachment_ids'] = [Command.set([pdf_attachment_id])]

        return {
            'name': _("Send Telegram Message"),
            'type': 'ir.actions.act_window',
            'res_model': 'telegram.test',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx
        }
