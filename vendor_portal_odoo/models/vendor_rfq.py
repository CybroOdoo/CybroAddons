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
from odoo import api, fields, models, _


class VendorRFQ(models.Model):
    """Vendor RFQ model"""
    _name = 'vendor.rfq'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vendor RFQ'

    name = fields.Char('RFQ Reference', required=True, index=True,
                       help="Name", copy=False, default=lambda x: _('New'))
    product_id = fields.Many2one('product.product', string='Product',
                                 help="Select Product")
    quantity = fields.Float(string="Quantity", help="Quantity Required")
    uom_id = fields.Many2one('uom.uom', string='UoM', help="UOM")
    estimated_quote = fields.Monetary("Estimated Quote",
                                      currency_field='currency_id',
                                      help="Estimated Quote Price")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  help="Currency",
                                  required=True,
                                  default=lambda
                                      self: self.env.company.currency_id)
    notes = fields.Html(string='Notes', help="Additional Note")
    estimated_delivery_date = fields.Date(string="Delivery date",
                                          help="Vendor's delivery date")
    quote_date = fields.Date(default=fields.Date.context_today, help="Quote Date")
    closing_date = fields.Date(string="Closing date",
                               help="Quotation closing date")
    vendor_ids = fields.Many2many('res.partner',
                                  domain="[('is_registered', '=', True)]",
                                  help="Vendors you want to send quotations")
    vendor_quote_history_ids = fields.One2many('vendor.quote.history',
                                               'quote_id',
                                               string="Vendor Quote History",
                                               help="Vendor Quote History")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user,
                              string="Responsible", help="Responsible Person")
    approved_vendor_id = fields.Many2one('res.partner', string="Approved Vendor", help="Approved Vendor")
    order_id = fields.Many2one('purchase.order', string='Order ID', help="Order ID")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'), ('order', 'Purchase Order'),
    ], string="Status", default='draft', help="Different stages")
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, help="Select Company"
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set default UoM when product is changed"""
        if self.product_id:
            self.uom_id = self.product_id.uom_id

    @api.model_create_multi
    def create(self, vals_list):
        """Override the create method to assign a unique sequence to the
        'name' field and default uom_id."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'vendor.rfq') or '/'
            if vals.get('product_id') and not vals.get('uom_id'):
                product = self.env['product.product'].browse(vals['product_id'])
                vals['uom_id'] = product.uom_id.id
        return super().create(vals_list)

    def write(self, vals):
        """Update uom_id if product_id is changed and uom_id not specified."""
        if vals.get('product_id') and 'uom_id' not in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['uom_id'] = product.uom_id.id
        return super().write(vals)

    def action_send_by_mail(self):
        """This method sends an email to each vendor listed in the `vendor_ids`
        field, using a predefined email template. The template is personalized
        with the vendor's name and language. The email is sent from the current
        user's email address."""
        template = self.env.ref(
            'vendor_portal_odoo.email_template_vendor_rfq_request')
        for vendor in self.vendor_ids:
            context = {
                'name': vendor.name,
                'lang': vendor.lang,
                'partner_to': vendor.id,
            }
            email_values = {
                'email_to': vendor.email,
                'email_from': self.env.user.partner_id.email,
            }
            template.with_context(
                context).send_mail(self.id, email_values=email_values,
                                   force_send=True)
        self.state = 'in_progress'

    def action_pending(self):
        """For changing state to pending"""
        self.state = 'pending'

    def action_cancel(self):
        """For changing state to cancel"""
        self.state = 'cancel'

    def action_done(self):
        """For mark as done"""

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'rfq.done',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {'default_quote_ids': self.vendor_quote_history_ids.ids},
        }

    def action_create_quotation(self):
        """For creating purchase RFQ from vendor quotations"""
        self.ensure_one()
        rfq_quote = self.env['vendor.quote.history'].search([
            ('vendor_id', '=', self.approved_vendor_id.id),
            ('quote_id', '=', self.id)], limit=1)
        price = rfq_quote.quoted_price if rfq_quote else 0.0
        uom = self.uom_id or self.product_id.uom_id
        order = self.env['purchase.order'].sudo().create({
            'partner_id': self.approved_vendor_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product_id.display_name or self.product_id.name,
                    'product_id': self.product_id.id,
                    'product_qty': self.quantity,
                    'uom_id': uom.id if uom else False,
                    'price_unit': price,
                    'date_planned': rfq_quote.estimate_date if rfq_quote else fields.Date.today(),
                    'tax_ids': [(6, 0, self.product_id.supplier_taxes_id.ids)],
                })],
        })
        self.write({
            'state': 'order',
            'order_id': order.id
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': order.id,
            'target': 'current',
            'views': [(False, 'form')],
        }

    def set_rfq_done(self):
        """Set the RFQ as done"""
        quotes = self.search([('state', '=', 'in_progress'),
                              ('vendor_quote_history_ids',
                               '!=', False),
                              ('closing_date', '<=',
                               fields.Date.today())])
        if quotes:
            rfq_done_based_on = self.env['ir.config_parameter'].sudo().get_str(
                'vendor_portal_odoo.rfq_done_based_on')
            for rec in quotes:
                order = 'estimate_date asc' if rfq_done_based_on == 'based_on_delivery_time' else 'quoted_price asc'
                vendor_quotes = self.env['vendor.quote.history'].search([
                    ('quote_id', '=', rec.id),
                ], limit=1, order=order)
                if vendor_quotes:
                    rec.write({
                        'approved_vendor_id': vendor_quotes.vendor_id.id,
                        'state': 'done'
                    })

    def get_purchase_order(self):
        """Retrieve the purchase order associated with the current record."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': self.order_id.id,
            'target': 'current',
            'views': [(False, 'form')],
        }
