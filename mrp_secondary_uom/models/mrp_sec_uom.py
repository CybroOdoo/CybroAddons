# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nikhil krishnan(<http://www.cybrosys.com>)
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

from openerp import models, fields, api


class MRPSecUOM(models.Model):
    _inherit = 'mrp.production'

    # name = fields.Char('Reference', required=True, readonly=True, states={'draft': [('readonly', False)]}, copy=False)

    def compute_to_produce_product(self):
        for s in self:
            if s.move_created_ids:
                for moves in s.move_created_ids:
                    s.to_produce_product += moves.product_uom_qty
            else:
                s.to_produce_product = 0

    def compute_produced_product(self):
        for s in self:
            if s.move_created_ids2:
                for moves in s.move_created_ids2:
                    if moves.state != 'cancel':
                        s.produced_product += moves.product_uom_qty
            else:
                s.produced_product = 0

    def compute_to_produce_product2(self):
        for s in self:
            if s.move_created_ids:
                for moves in s.move_created_ids:
                    s.to_produce_product2 += moves.stock_move_sec_qty
            else:
                s.to_produce_product2 = 0

    def compute_produced_product2(self):
        for s in self:
            if s.move_created_ids2:
                for moves in s.move_created_ids2:
                    s.produced_product2 += moves.stock_move_sec_qty
            else:
                s.produced_product2 = 0

    mrp_sec_qty = fields.Float('Secondary Quantity', readonly=True, states={'draft': [('readonly', False)]})
    mrp_sec_uom = fields.Many2one('product.uom', 'Secondary Unit', readonly=True,
                                  states={'draft': [('readonly', False)]})
    to_produce_product = fields.Float('Product To produce', compute="compute_to_produce_product")
    produced_product = fields.Float('Produced Products', compute="compute_produced_product")
    to_produce_product2 = fields.Float('Product To produce(2ndry)')
    produced_product2 = fields.Float('Produced Products(2ndry)')

    def _make_production_produce_line(self, cr, uid, production, context=None):

        stock_move = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        source_location_id = production.product_id.property_stock_production.id
        destination_location_id = production.location_dest_id.id
        procs = proc_obj.search(cr, uid, [('production_id', '=', production.id)], context=context)
        procurement = procs and\
            proc_obj.browse(cr, uid, procs[0], context=context) or False
        # To Find the ratio of Primary and sec UOM Qty
        if production.product_qty:
            ratio = production.mrp_sec_qty/production.product_qty
        else:
            ratio = 0
        data = {
            'name': production.name,
            'date': production.date_planned,
            'date_expected': production.date_planned,
            'product_id': production.product_id.id,
            'product_uom': production.product_uom.id,
            'product_uom_qty': production.product_qty,
            'stock_move_sec_qty': production.mrp_sec_qty,
            'stock_move_sec_uom': production.mrp_sec_uom.id,
            'ratio_sec_uom': ratio,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'move_dest_id': production.move_prod_id.id,
            'procurement_id': procurement and procurement.id,
            'company_id': production.company_id.id,
            'production_id': production.id,
            'origin': production.name,
            'group_id': procurement and procurement.group_id.id,
        }
        move_id = stock_move.create(cr, uid, data, context=context)
        return stock_move.action_confirm(cr, uid, [move_id], context=context)[0]


class StockMoveSecUOM(models.Model):
    _inherit = 'stock.move'

    stock_move_sec_qty = fields.Float('2ndry Quantity', compute='compute_stock_move_sec_qty')
    stock_move_sec_uom = fields.Many2one('product.uom', '2ndry Unit')
    ratio_sec_uom = fields.Float('Ratio 2ndry Quantity')

    def compute_stock_move_sec_qty(self):
        for rec in self:
            rec.stock_move_sec_qty = rec.ratio_sec_uom * rec.product_qty
            

class MRPProductProduceSecUOM(models.TransientModel):
    _inherit = 'mrp.product.produce'

    def _get_product_uom(self, cr, uid, context=None):

        if context is None:
            context = {}
        prod = self.pool.get('mrp.production').browse(cr, uid,
                                context['active_id'], context=context)
        return prod.product_uom.id

    def _get_product_produce_sec_uom(self, cr, uid, context=None):

        if context is None:
            context = {}
        prod = self.pool.get('mrp.production').browse(cr, uid,
                                context['active_id'], context=context)
        return prod.mrp_sec_uom.id

    def _get_product_produce_sec_qty(self, cr, uid, context=None):

        if context is None:
            context = {}
        prod = self.pool.get('mrp.production').browse(cr, uid,
                                context['active_id'], context=context)
        done = 0.0
        for move in prod.move_created_ids2:
            if move.product_id == prod.product_id:
                if not move.scrapped:
                    done += move.product_uom_qty
        select_qty = prod.product_qty - done
        return (prod.mrp_sec_qty/prod.product_qty) * select_qty
        # return prod.to_produce_product2

    product_uom = fields.Many2one('product.uom')
    product_produce_sec_qty = fields.Float('2ndry Quantity')
    product_produce_sec_uom = fields.Many2one('product.uom', '2ndry UoM')

    _defaults = {
        'product_uom': _get_product_uom,
        'product_produce_sec_qty': _get_product_produce_sec_qty,
        'product_produce_sec_uom': _get_product_produce_sec_uom,
    }

    @api.multi
    def do_produce(self):
        result = super(MRPProductProduceSecUOM, self).do_produce()
        mrp_prod_obj = self.env['mrp.production'].browse(
            self.env.context['active_id'])
        for data in self:
            to_produce = mrp_prod_obj.to_produce_product2 - data.product_produce_sec_qty
            produced = mrp_prod_obj.produced_product2 + data.product_produce_sec_qty
            mrp_prod_obj.write({'to_produce_product2': to_produce})
            mrp_prod_obj.write({'produced_product2': produced})
        return result

    def on_change_qty(self, cr, uid, ids, product_qty, consume_lines, context=None):
        res = super(MRPProductProduceSecUOM, self).on_change_qty(cr, uid, ids, product_qty, consume_lines,
                                                                 context=context)
        rec = self.browse(cr, uid, context['active_id'], context=context)
        prod = self.pool.get('mrp.production').browse(cr, uid, context['active_id'], context=context)

        if prod.product_qty != 0:
            valss = (prod.mrp_sec_qty/prod.product_qty) * product_qty
            res['value']['product_produce_sec_qty'] = valss
        return res

