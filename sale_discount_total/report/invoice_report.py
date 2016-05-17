from openerp.osv import fields, osv


class DiscountInvoiceReport(osv.osv):
    _inherit = 'account.invoice.report'

    _columns = {
        'discount': fields.float('Discount', readonly=True),
    }

    def _select(self):
        res = super(DiscountInvoiceReport,self)._select()
        select_str = res + """, sub.discount / cr.rate as discount """
        return select_str

    def _sub_select(self):
        res = super(DiscountInvoiceReport,self)._sub_select()
        select_str = res + """,SUM(CASE
            WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
            THEN - ((ail.quantity / u.factor * u2.factor) * ail.price_unit * (ail.discount) / 100.0)
            ELSE ((ail.quantity / u.factor * u2.factor) * ail.price_unit * (ail.discount) / 100.0) END) as discount"""
        return select_str
