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
from odoo import _, Command, api, fields, models
from odoo.exceptions import UserError, ValidationError


class WebsitePrebook(models.Model):
    """Store website pre-bookings and their linked sale orders."""
    _name = 'website.prebook'
    _description = 'Website PreBooking'
    _rec_name = 'reference'

    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        help='Customer who placed the pre-booking.',
    )
    booking_date = fields.Date(
        'Booking Date', required=True, default=fields.Date.context_today,
        help='Date the pre-booking was placed.',
    )
    product_id = fields.Many2one(
        'product.template', string='Product', required=True,
        help='Product being pre-booked.',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ], string='Status', default='draft', help='Status of the pre-booking.'
    )
    website_id = fields.Many2one(
        "website",
        string='Website',
        ondelete='restrict',
        index=True,
        readonly=True, help='Website where the pre-booking was placed.'
    )
    reference = fields.Char(string='Reference', required=True, copy=False,
                            readonly=True,
                            default='New')
    sale_id = fields.Many2one(
        'sale.order', string='Sale Order', copy=False,
        help='Sale order generated from this pre-booking.',
    )
    quantity = fields.Integer(
        string='Quantity', required=True,
        help='Number of units reserved by the customer.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign a unique sequence reference to each new booking."""
        for vals in vals_list:
            if not vals.get('reference') or vals['reference'] == 'New':
                seq = (
                    self.env['ir.sequence'].next_by_code('website.prebook')
                    or 'New'
                )
                vals['reference'] = seq
        return super().create(vals_list)

    @api.constrains('quantity')
    def _check_quantity(self):
        for booking in self:
            if booking.quantity <= 0:
                raise ValidationError(
                    _('The pre-booking quantity must be greater than zero.')
                )

    def action_confirm(self):
        """Create one sale order for each unconfirmed booking."""
        for booking in self:
            if booking.sale_id:
                continue
            if (
                not booking.partner_id
                or not booking.product_id
                or booking.quantity <= 0
            ):
                raise UserError(
                    _('A customer, product, and positive quantity are'
                      ' required.')
                )
            sale_order = self.env['sale.order'].create({
                'partner_id': booking.partner_id.id,
                'website_id': booking.website_id.id,
                'order_line': [Command.create({
                    'product_id': booking.product_id.product_variant_id.id,
                    'product_uom_qty': booking.quantity,
                })],
            })
            booking.write({
                'sale_id': sale_order.id,
                'state': 'confirm',
            })

    def action_view_sale_order(self):
        """Open the sale order linked to this booking."""
        self.ensure_one()
        if not self.sale_id:
            raise UserError(_('This pre-booking has no sale order yet.'))
        return {
            'name': _('Sale Order'),
            'view_mode': 'form',
            'view_id': self.env.ref('sale.view_order_form').id,
            'res_id': self.sale_id.id,
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
        }
