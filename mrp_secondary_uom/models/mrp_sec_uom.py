# -*- coding: utf-8 -*-
#
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class MRPSecUOM(models.Model):
    _inherit = 'mrp.production'

    mrp_sec_qty = fields.Float('Secondary Quantity', readonly=True)
    mrp_sec_uom = fields.Many2one('product.uom', 'Secondary Unit')
    mrp_ratio_sec_uom = fields.Float('Ratio 2ndry Quantity', digits=dp.get_precision('Secondary UoM Ratio'))

    # Over write this fuction for add the new line of code: 'ratio_sec_uom': self.mrp_ratio_sec_uom,
    def _generate_finished_moves(self):
        move = self.env['stock.move'].create({
            'name': self.name,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.product_qty,
            'ratio_sec_uom': self.mrp_ratio_sec_uom,
            'stock_move_sec_uom': self.mrp_sec_uom.id,
            'location_id': self.product_id.property_stock_production.id,
            'location_dest_id': self.location_dest_id.id,
            'move_dest_id': self.procurement_ids and self.procurement_ids[0].move_dest_id.id or False,
            'procurement_id': self.procurement_ids and self.procurement_ids[0].id or False,
            'company_id': self.company_id.id,
            'production_id': self.id,
            'origin': self.name,
            'group_id': self.procurement_group_id.id,
        })
        move.action_confirm()
        return move

    @api.model
    def create(self, vals):
        if vals.get('mrp_sec_qty'):
            if vals.get('product_qty'):
                vals['mrp_ratio_sec_uom'] = float(vals['mrp_sec_qty'])/float(vals['product_qty'])
        return super(MRPSecUOM, self).create(vals)


class StockMoveSecUOM(models.Model):
    _inherit = 'stock.move'

    stock_move_sec_qty_to_produce = fields.Float(string='To Produce (2ndry)',
                                                 compute='compute_stock_move_sec_qty_to_produce')
    stock_move_sec_uom = fields.Many2one('product.uom', string='2ndry UoM')
    stock_move_sec_qty_produced = fields.Float(string='Produced (2ndry)',
                                               compute='compute_stock_move_sec_qty_produced')
    ratio_sec_uom = fields.Float(string='Ratio 2ndry Quantity', digits=dp.get_precision('Secondary UoM Ratio'))

    def compute_stock_move_sec_qty_to_produce(self):
        for rec in self:
            rec.stock_move_sec_qty_to_produce = rec.ratio_sec_uom * rec.product_uom_qty

    def compute_stock_move_sec_qty_produced(self):
        for rec in self:
            rec.stock_move_sec_qty_produced = rec.ratio_sec_uom * rec.quantity_done


class MRPProductProduceSecUOM(models.TransientModel):
    _inherit = 'mrp.product.produce'

    product_produce_sec_qty = fields.Float(string='2ndry Quantity')
    ratio_sec_uom = fields.Float(string='Ratio 2ndry Quantity', digits=dp.get_precision('Secondary UoM Ratio'))
    product_produce_sec_uom = fields.Many2one('product.uom', string='2ndry UoM')

    @api.model
    def default_get(self, fields):
        res = super(MRPProductProduceSecUOM, self).default_get(fields)
        if self._context and self._context.get('active_id'):
            production = self.env['mrp.production'].browse(self._context['active_id'])
            serial_finished = (production.product_id.tracking == 'serial')
            if serial_finished:
                sec_qty = production.mrp_ratio_sec_uom
            else:

                sec_qty = res['product_qty'] * production.mrp_ratio_sec_uom

            res['product_produce_sec_qty'] = sec_qty
            res['product_produce_sec_uom'] = production.mrp_sec_uom.id
            res['ratio_sec_uom'] = production.mrp_ratio_sec_uom
        return res

    @api.onchange('product_qty', 'product_produce_sec_qty')
    def onchange_product_qty(self):
        sec_qty = self.product_qty * self.ratio_sec_uom
        self.product_produce_sec_qty = sec_qty
