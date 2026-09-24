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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api

class TelegramTest(models.TransientModel):
    """Wizard to send a test Telegram message."""
    _name = "telegram.test"
    _description = "Send Telegram Test Message"

    partner_id = fields.Many2one(
        'res.partner',
        string="Partner",
        required=True,
        help="Contact to whom the Telegram message will be sent."
    )

    message_text = fields.Text(
        string="Message",
        required=True,
        default="This is a test message from Odoo.",
        help="Message content to be sent through Telegram."
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        help="Related sales order used for sending template-based messages."
    )

    purchase_order_id = fields.Many2one(
        'purchase.order',
        string="Purchase Order",
        help="Related purchase order used for sending template-based messages."
    )

    invoice_id = fields.Many2one(
        'account.move',
        string="Invoice",
        help="Related invoice used for sending template-based messages."
    )

    picking_id = fields.Many2one(
        'stock.picking',
        string="Delivery Order",
        help="Related delivery order used for sending template-based messages."
    )

    telegram_template_id = fields.Many2one(
        'telegram.template',
        string='Telegram Template',
        domain="[('model_id', '=', current_model_id)]",
        help="Select a Telegram template compatible with the current document type."
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help="Files to be sent along with the Telegram message."
    )

    current_model_id = fields.Many2one(
        'ir.model',
        compute='_compute_current_model',
        store=False,
        help="Technical field used to determine which templates are available."
    )

    @api.model
    def default_get(self, fields_list):
        """
        Populate default values for the Telegram message wizard by checking the active
        document in the context and pre-filling the attachment.
        """
        res = super(TelegramTest, self).default_get(fields_list)
        if 'attachment_ids' in fields_list:
            res_model, res_id = False, False
            if self.env.context.get('default_sale_order_id'):
                res_model, res_id = 'sale.order', self.env.context.get('default_sale_order_id')
            elif self.env.context.get('default_purchase_order_id'):
                res_model, res_id = 'purchase.order', self.env.context.get('default_purchase_order_id')
            elif self.env.context.get('default_invoice_id'):
                res_model, res_id = 'account.move', self.env.context.get('default_invoice_id')
            elif self.env.context.get('default_picking_id'):
                res_model, res_id = 'stock.picking', self.env.context.get('default_picking_id')
                
            if res_model and res_id:
                attachment = self.env['ir.attachment'].search([
                    ('res_model', '=', res_model),
                    ('res_id', '=', res_id),
                    ('mimetype', '=', 'application/pdf')
                ], order='id desc', limit=1)
                if attachment:
                    res['attachment_ids'] = [(6, 0, attachment.ids)]
        return res

    @api.depends('sale_order_id', 'purchase_order_id', 'invoice_id', 'picking_id')
    def _compute_current_model(self):
        """Determine the related document model from active fields to filter templates."""
        for rec in self:
            model_name = 'res.partner'
            if rec.sale_order_id:
                model_name = 'sale.order'
            elif rec.purchase_order_id:
                model_name = 'purchase.order'
            elif rec.invoice_id:
                model_name = 'account.move'
            elif rec.picking_id:
                model_name = 'stock.picking'

            rec.current_model_id = self.env['ir.model'].search(
                [('model', '=', model_name)],
                limit=1
            )

    @api.onchange('sale_order_id', 'purchase_order_id', 'invoice_id', 'picking_id')
    def _onchange_current_model(self):
        """Dynamically update the domain for 'telegram_template_id' based on the current model."""
        self._compute_current_model()
        domain = [('model_id', '=', self.current_model_id.id)] if self.current_model_id else []
        return {'domain': {'telegram_template_id': domain}}

    def action_send(self):
        """
        Execute the action to send the configured message and attachments via Telegram,
        delegating to the corresponding document model.
        """
        self.ensure_one()
        if self.sale_order_id:
            return self.sale_order_id.send_telegram_message(self.message_text, self.telegram_template_id, attachment_ids=self.attachment_ids.ids)
        elif self.purchase_order_id:
            return self.purchase_order_id.send_telegram_message(self.message_text, self.telegram_template_id, attachment_ids=self.attachment_ids.ids)
        elif self.invoice_id:
            return self.invoice_id.send_telegram_message(self.message_text, self.telegram_template_id, attachment_ids=self.attachment_ids.ids)
        elif self.picking_id:
            return self.picking_id.send_telegram_message(self.message_text, self.telegram_template_id, attachment_ids=self.attachment_ids.ids)
        
        return self.partner_id.send_telegram_message(self.message_text, self.telegram_template_id, attachment_ids=self.attachment_ids.ids)

    @api.onchange('telegram_template_id')
    def _onchange_telegram_template_id(self):
        """Automatically populate or clear the message text based on the selected template."""
        if self.telegram_template_id:
            self.message_text = self.telegram_template_id.message
        else:
            self.message_text = ""
