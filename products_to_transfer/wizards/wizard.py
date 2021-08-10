# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mehjabin Farsana (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from odoo import models, fields, api
from datetime import timedelta


class TransferProductDetailsWizard(models.TransientModel):
    _name = 'transfer.products.details.wizard'
    _description = 'Wizard to View Product Details from Inventory Transfer'

    def _get_default_picking_id(self):
        picking_id = self.env['stock.picking'].browse(self._context.get('picking_id'))
        return picking_id.name

    product_id = fields.Char(string="Product", readonly=True)
    qty = fields.Float(string="Quantity")
    picking_id = fields.Char(string="Picking", readonly=True, default=_get_default_picking_id)
    transfer_history_ids = fields.One2many('product.transfer.history', 'product_details_id', string="Transfer History", readonly=True)
    date_from = fields.Date(string="Transfer History From", default=fields.Date.today() - timedelta(days=30), required=True)

    @api.onchange('date_from')
    def _onchange_date_from(self):
        move_ids = self.env['stock.move'].search([('product_id', '=', self._context.get('active_id')),
                                                   ('state', '=', 'done'), ('picking_id.date_done', '>=', self.date_from)])
        vals = []
        for move in move_ids:
            vals.append((0, 0, {
                'date_picking': move.date,
                'partner_id': move.picking_id.partner_id.id,
                'qty': move.product_uom_qty,
                'picking_id': move.picking_id.name

            }))
        self.transfer_history_ids = vals

    def add_to_transfer(self):

        picking_id = self.env['stock.picking'].browse(self._context.get('picking_id'))

        product_id = self.env['product.product'].browse(self._context.get('active_id'))
        display_name = product_id.name_get()[0][1]
        if product_id.description_sale:
            display_name += '\n' + product_id.description_sale
        vals = {
            'product_id': product_id.id,
            'name': display_name,
            'product_uom_qty': self.qty,
            'product_uom': product_id.uom_id.id,
            'location_id': picking_id.location_id.id,
            'location_dest_id': picking_id.location_dest_id.id,
            'picking_id': picking_id.id
        }
        self.env['stock.move'].create(vals)


class ProductTransferHistory(models.TransientModel):
    _name = 'product.transfer.history'
    _description = 'Product Transfer History Wizard'

    date_picking = fields.Datetime(string="Date")
    picking_id = fields.Char(string="Transfer")
    partner_id = fields.Many2one('res.partner', string="Contact")
    qty = fields.Float(string="Quantity")
    product_details_id = fields.Many2one('transfer.products.details.wizard')
