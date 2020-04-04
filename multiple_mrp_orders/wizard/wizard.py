# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nimisha Muralidhar (odoo@cybrosys.com)
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
from odoo import models, fields, api, _


class MrpProductWizard(models.TransientModel):
    _name = 'mrp.product.produce.wizard'

    produce_line_ids = fields.One2many('mrp.product.produce.wizard.line', 'product_produce_id',
                                       string='Product to Track')

    # Method to check availability and produce the products for mrp orders
    def action_check_availability_produce(self):
        for line in self.produce_line_ids.mapped('production_id'):
            line.with_context({'active_id': line.id,
                               'active_ids': [line.id],
                               }).action_assign()
            for move_line in line.move_raw_ids:
                move_line.quantity_done = move_line.product_uom_qty
            produce_wizard = self.env['mrp.product.produce'].with_context({
                'active_id': line.id,
                'active_ids': [line.id],
            }).create({
                'qty_producing': line.product_qty,
            })
            produce_wizard.do_produce()

    # Method to mark the mrp orders as done
    def action_done(self):
        for line in self.produce_line_ids.mapped('production_id'):
            line.button_mark_done()


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Method for the wizard check availability and produce
    def action_product_availability_produce_show_wizard(self):
        production_ids = self.env['mrp.production'].browse(self._context.get('active_ids', False))
        lines = []
        for line in production_ids:
            vals = (0, 0, {
                'production_id': line.id,
                'product_id': line.product_id.id,
                'qty': line.product_qty
            })
            lines.append(vals)
        return {'type': 'ir.actions.act_window',
                'name': _('Produce'),
                'res_model': 'mrp.product.produce.wizard',
                'target': 'new',
                'view_id': self.env.ref('multiple_mrp_orders.view_mrp_product_availability_wizard').id,
                'view_mode': 'form',
                'context': {'default_produce_line_ids': lines}
                }

    # Method for the wizard Mark as Done
    def action_done_show_wizard(self):
        production_ids = self.env['mrp.production'].browse(self._context.get('active_ids', False))
        lines = []
        for line in production_ids:
            vals = (0, 0, {
                'production_id': line.id,
                'product_id': line.product_id.id,
                'qty': line.product_qty
            })
            lines.append(vals)
        return {'type': 'ir.actions.act_window',
                'name': _('Mark as Done'),
                'res_model': 'mrp.product.produce.wizard',
                'target': 'new',
                'view_id': self.env.ref('multiple_mrp_orders.view_mrp_product_done_wizard').id,
                'view_mode': 'form',
                'context': {'default_produce_line_ids': lines}
                }


class MrpProductProduceWizardLine(models.TransientModel):
    _name = "mrp.product.produce.wizard.line"
    _description = "Record Production Line"

    product_produce_id = fields.Many2one('mrp.product.produce.wizard')
    production_id = fields.Many2one('mrp.production')
    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float('Quantity')
