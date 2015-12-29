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
            val = val1 = val2 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            if order.discount_type == 'amount':
                val2 = order.discount_rate
            elif order.discount_type == 'percent':
                val2 = ((val1 + val) * order.discount_rate) / 100
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_discount'] = cur_obj.round(cr, uid, cur, val2)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] - \
                                            res[order.id]['amount_discount']
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
        'discount_rate': fields.float('Discount Amount', digits_compute=dp.get_precision('Account'),
                                      readonly=True,
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, ),
        'amount_discount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Discount',
                                           multi='sums', help="The total discount."),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'),
                                          string='Untaxed Amount',
                                          multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
                                      multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
                                        multi='sums', help="The total amount."),
    }

    _defaults = {
        'discount_type': 'percent',
    }

    @api.onchange('discount_type', 'discount_rate')
    def compute_discount(self):
        for order in self:
            val1 = val2 = 0.0
            for line in order.order_line:
                val1 += line.price_subtotal
                val2 += self._amount_line_tax(line)
            if order.discount_type == 'percent':
                if order.discount_rate == 100:
                    disc_amnt = val1 + val2
                else:
                    disc_amnt = (val1 + val2) * order.discount_rate / 100
                total = val1 + val2 - disc_amnt
                self.currency_id = order.pricelist_id.currency_id
                self.amount_discount = disc_amnt
                self.amount_total = total
            else:
                total = (val1 + val2) - order.discount_rate
                self.currency_id = order.pricelist_id.currency_id
                self.amount_discount = order.discount_rate
                self.amount_total = total

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(SaleOrder, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals.update({
            'discount_type': order.discount_type,
            'discount_rate': order.discount_rate
        })
        return invoice_vals
