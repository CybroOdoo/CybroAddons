from openerp import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    discount = fields.Float('Discount', readonly=True)

    def _select(self):
        res = super(AccountInvoiceReport,self)._select()
        select_str = res + """, sub.discount AS discount """
        return select_str

    def _sub_select(self):
        res = super(AccountInvoiceReport,self)._sub_select()
        select_str = res + """,SUM(CASE
            WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
            THEN - ((ail.quantity / u.factor * u2.factor) * ail.price_unit * (ail.discount) / 100.0)
            ELSE ((ail.quantity / u.factor * u2.factor) * ail.price_unit * (ail.discount) / 100.0) END) as discount"""
        return select_str