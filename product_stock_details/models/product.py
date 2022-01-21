# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_stock_location = fields.One2many('product.stock.location', 'product_id')
    is_location = fields.Boolean(compute="get_location_details")

    def get_location_details(self):
        locations = self.env['stock.quant'].search([('product_id', '=', self.id)])
        vals = []
        for rec in locations:
            vals.append((0, 0, {
                'product_id': self.id,
                'location_id': rec.location_id.id,
                'available_quantity': rec.available_quantity,
                'virtual_available': rec.virtual_available,
                'incoming_qty': rec.incoming_qty,
                'outgoing_qty': rec.outgoing_qty,
            }))
        self.product_stock_location = [(5, 0, 0)]
        self.product_stock_location = vals
        self.is_location = True

    def get_wo_description(self):
        return self.env.ref('product_stock_details.action_report_followup_community').report_action(self, data='')


class ProjectEmployeeLine(models.Model):
    _name = "product.stock.location"

    product_id = fields.Many2one('product.product', string="Product")
    location_id = fields.Many2one('stock.location', string="Location")
    available_quantity = fields.Float(string="Available Qty")
    virtual_available = fields.Float(string="Forecasted Qty")
    incoming_qty = fields.Float(string="Incoming")
    outgoing_qty = fields.Float(string="Outgoing")
