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

from openerp.osv import fields, osv
from openerp.tools.translate import _


class ChangeProductionQty(osv.osv_memory):
    _inherit = 'change.production.qty'

    _columns = {
        'mrp_sec_qty': fields.float('Product Secondary Qty'),
        'mrp_sec_uom': fields.many2one('product.uom', 'Secondary Unit'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(ChangeProductionQty, self).default_get(cr, uid, fields, context=context)
        prod_obj = self.pool.get('mrp.production')
        prod = prod_obj.browse(cr, uid, context.get('active_id'), context=context)
        if 'product_qty' in fields:
            res.update({'product_qty': prod.product_qty})
        if 'mrp_sec_qty' in fields:
            res.update({'mrp_sec_qty': prod.mrp_sec_qty})
        if 'mrp_sec_uom' in fields:
            res.update({'mrp_sec_uom': prod.mrp_sec_uom.id})
        return res

    def _update_product_to_produce(self, cr, uid, prod, qty, sec_qty, sec_uom, context=None):
        move_lines_obj = self.pool.get('stock.move')
        ratio = sec_qty/qty
        for m in prod.move_created_ids:
            move_lines_obj.write(cr, uid, [m.id], {'product_uom_qty': qty, 'stock_move_sec_uom': sec_uom.id,
                                                   'stock_move_sec_qty': sec_qty, 'ratio_sec_uom': ratio})

    def change_prod_qty(self, cr, uid, ids, context=None):

        """
        Changes the Quantity of Product, and Secondary Quantity of Product And Uom
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        @return:
        """
        record_id = context and context.get('active_id', False)
        assert record_id, _('Active Id not found')
        prod_obj = self.pool.get('mrp.production')
        bom_obj = self.pool.get('mrp.bom')
        move_obj = self.pool.get('stock.move')
        for wiz_qty in self.browse(cr, uid, ids, context=context):
            prod = prod_obj.browse(cr, uid, record_id, context=context)
            print "LLLL", prod
            prod_obj.write(cr, uid, [prod.id], {'product_qty': wiz_qty.product_qty,
                                                'mrp_sec_qty': wiz_qty.mrp_sec_qty,
                                                'mrp_sec_uom': wiz_qty.mrp_sec_uom.id,
                                                })
            prod_obj.action_compute(cr, uid, [prod.id])

            for move in prod.move_lines:
                bom_point = prod.bom_id
                bom_id = prod.bom_id.id
                if not bom_point:
                    bom_id = bom_obj._bom_find(cr, uid, product_id=prod.product_id.id, context=context)
                    if not bom_id:
                        raise osv.except_osv(_('Error!'), _("Cannot find bill of material for this product."))
                    prod_obj.write(cr, uid, [prod.id], {'bom_id': bom_id})
                    bom_point = bom_obj.browse(cr, uid, [bom_id])[0]

                if not bom_id:
                    raise osv.except_osv(_('Error!'), _("Cannot find bill of material for this product."))

                factor = prod.product_qty * prod.product_uom.factor / bom_point.product_uom.factor
                product_details, workcenter_details = \
                    bom_obj._bom_explode(cr, uid, bom_point, prod.product_id, factor / bom_point.product_qty, [], context=context)
                for r in product_details:
                    if r['product_id'] == move.product_id.id:
                        move_obj.write(cr, uid, [move.id], {'product_uom_qty': r['product_qty']})
            if prod.move_prod_id:
                print "LOLLOLprod.move_prod_idprod.move_prod_idOLO", prod.move_prod_id
                move_obj.write(cr, uid, [prod.move_prod_id.id], {'product_uom_qty':  wiz_qty.product_qty})
            self._update_product_to_produce(cr, uid, prod, wiz_qty.product_qty, wiz_qty.mrp_sec_qty,
                                            wiz_qty.mrp_sec_uom, context=context)
        return {}
