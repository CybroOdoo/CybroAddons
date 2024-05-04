# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

from odoo import api, fields, models, _


class WebsitePrebook(models.Model):
    """ class for defining website.prebook model"""
    _name = 'website.prebook'
    _rec_name = 'reference'

    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help="Add the customer name")
    booking_date = fields.Date('Booking Date', help="Pre booking date")
    product_id = fields.Many2one('product.template', string="Product",
                                 help="Add the product")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ], string='Status', default='draft', help="state of pre-booking"
    )
    website_id = fields.Many2one(
        "website",
        string="Website",
        ondelete="restrict",
        index=True,
        readonly=True, help="name of the website"
    )
    reference = fields.Char(string='Reference', required=True, copy=False,
                            readonly=True,
                            default=lambda self: _('New'))
    sale_id = fields.Many2one('sale.order', string='Sale order',
                              help="sale order")

    @api.model
    def create(self, vals):
        """Supering create function for creating sequence"""
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('prebook.sequence') or _('New')
        return super(WebsitePrebook, self).create(vals)

    def action_confirm(self):
        """sale order creation while confirming the button"""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'website_id': self.website_id.id,
            'order_line': [(0, 0, {
                'product_template_id': self.product_id.id,
                'product_id': self.product_id.product_variant_id.id,
                'name': self.product_id.product_variant_id.name,
                'product_uom_qty': 1,
            })],
        })
        self.sale_id = sale_order.id
        self.state = 'confirm'

    def action_view_sale_order(self):
        """Smart button view function"""
        return {
            'name': 'Sale Order',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('sale.view_order_form').id,
            'res_id': self.sale_id.id,
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
        }
