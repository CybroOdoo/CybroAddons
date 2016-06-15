from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp


class DiscountSaleReport(osv.osv):
    _inherit = 'sale.report'

    _columns = {
        'discount': fields.float('Discount', readonly=True, digits=dp.get_precision('Discount')),
    }

    def _select(self):
        res = super(DiscountSaleReport,self)._select()
        select_str = res+""",sum(l.product_uom_qty * cr.rate * l.price_unit * (l.discount) / 100.0) as discount"""
        return select_str
