# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class ProductRfq(models.TransientModel):
    """ Model product.rfq """
    _name = 'product.rfq'
    _description = 'Product RFQ'
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', string="Sales Person", required=True,
                              default=lambda self: self.env.user,
                              help="Sales Person for RFQ")
    partner_id = fields.Many2one('res.partner', string="Vendor",
                                 help="Vendor for RFQ")
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env.company)
    date_order = fields.Datetime('Order Deadline', required=True,
                                 default=fields.Datetime.now,
                                 help="Depicts the date within which the "
                                      "Quotation should be confirmed and "
                                      "converted into a purchase order.")
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id')
    rfq_line_ids = fields.One2many('product.rfq.line', 'product_rfq_id',
                                   string="Product Lines", required=True)

    def action_create_view_rfq(self):
        """ Method to create rfq return the rfq """
        if not self.partner_id:
            raise UserError(_('Please Select a Vendor'))
        rfq = self._create_purchase_order()
        return {
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': rfq.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_create_rfq(self):
        """ Method to create rfq """
        if not self.partner_id:
            raise UserError(_('Please Select a Vendor'))
        self._create_purchase_order()

    def _create_purchase_order(self):
        return self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'date_order': self.date_order,
            'order_line': [(0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.display_name,
                'product_qty': line.product_qty,
                'price_unit': line.price_unit,
            }) for line in self.rfq_line_ids]
        })


class ProductRFQLine(models.TransientModel):
    """ Model product.rfq.line """
    _name = 'product.rfq.line'
    _description = 'Product RFQ Line'

    product_rfq_id = fields.Many2one('product.rfq', string="Product RFQ",
                                     help="Parent Product RFQ")
    product_id = fields.Many2one('product.product', string="Product",
                                 help="Order line Product")
    product_qty = fields.Float(string='Quantity', help="Order line Qty",
                               digits='Product Unit of Measure', required=True)
    price_unit = fields.Float(
        string='Unit Price', required=True, digits='Product Price',
        help="Order line Unit price")
