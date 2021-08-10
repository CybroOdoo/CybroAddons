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

from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_add_to_picking(self):
        active_id = self._context.get('active_id')
        picking_id = self.env['stock.picking'].browse(active_id)
        picking_id.write({
            'move_ids_without_package': [(0, 0, {
                'name': self.name,
                'product_id': self.id,
                'product_uom': self.uom_id.id,
                'product_uom_qty': 1,
                'location_id': picking_id.location_id.id,
                'location_dest_id': picking_id.location_dest_id.id,
            })],
        })

    def action_view_details(self):
        active_id = self._context.get('active_id')
        picking_id = self.env['stock.picking'].browse(active_id)
        res = {
            'name': 'Product Details',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'transfer.products.details.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'picking_id': picking_id.id,
                'default_product_id': self.name,
            }
            }
        return res
