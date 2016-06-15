from openerp.osv import fields, osv
from openerp import api
import openerp.addons.decimal_precision as dp


class SaleOrder(osv.Model):
    _inherit = 'sale.order'

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_discount': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            cur = order.pricelist_id.currency_id
            val1 = val2 = val3 = 0.0
            for line in order.order_line:
                val1 += line.price_subtotal
                val2 += self._amount_line_tax(cr, uid, line, context=context)
                val3 += (line.product_uom_qty * line.price_unit) * line.discount / 100
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val2)
            res[order.id]['amount_discount'] = cur_obj.round(cr, uid, cur, val3)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'discount_type': fields.selection([
            ('percent', 'Percentage'),
            ('amount', 'Amount')], 'Discount type'),
        'discount_rate': fields.float('Discount Rate', digits_compute=dp.get_precision('Account'),
                                      readonly=True,
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, ),
        'amount_discount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Discount',
                                           multi='sums', store=True, help="The total discount."),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'),
                                          string='Untaxed Amount',
                                          multi='sums', store=True, help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
                                      multi='sums', store=True, help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
                                        multi='sums', store=True, help="The total amount."),
    }

    _defaults = {
        'discount_type': 'percent',
    }

    @api.multi
    def compute_discount(self, discount):
        for order in self:
            val1 = val2 = 0.0
            disc_amnt = 0.0
            for line in order.order_line:
                val1 += (line.product_uom_qty * line.price_unit)
                line.discount = discount
                val2 += self._amount_line_tax(line)
                disc_amnt += (line.product_uom_qty * line.price_unit * line.discount)/100
            total = val1 + val2 - disc_amnt
            self.currency_id = order.pricelist_id.currency_id
            self.amount_discount = disc_amnt
            self.amount_tax = val2
            self.amount_total = total

    @api.onchange('discount_type', 'discount_rate')
    def supply_rate(self):
        for order in self:
            if order.discount_rate != 0:
                if order.discount_type == 'percent':
                    self.compute_discount(order.discount_rate)
                else:
                    total = 0.0
                    for line in order.order_line:
                        total += (line.product_uom_qty * line.price_unit)
                    discount = (order.discount_rate / total) * 100
                    self.compute_discount(discount)

    @api.multi
    def button_dummy(self):
        self.supply_rate()
        return True

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(SaleOrder, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals.update({
            'discount_type': order.discount_type,
            'discount_rate': order.discount_rate
        })
        return invoice_vals

class SaleOrderLine(osv.Model):
    _inherit = "sale.order.line"

    _columns = {
    'discount': fields.float(string='Discount (%)',
                            digits=(16, 10),
                            # digits= dp.get_precision('Discount'),
                            default=0.0),
    }