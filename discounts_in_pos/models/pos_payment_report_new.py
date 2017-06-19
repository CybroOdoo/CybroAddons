# -*- coding: utf-8 -*-

import time
from openerp.osv import osv
from openerp.report import report_sxw


class pos_payment_report_new(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(pos_payment_report_new, self).__init__(cr, uid, name, context=context)
        self.total = 0.0
        self.localcontext.update({
            'time': time,
            'pos_payment': self._pos_payment,
            'pos_payment_total':self._pos_payment_total,
            'pos_fixed_discount':self._pos_fixed_discount,
            'pos_percent_discount': self._pos_percent_discount,
        })

    def _pos_payment(self, obj):
        self.total = 0
        self.discount_total = 0
        self.discount_percent = 0
        data={}
        new_data={}
        sql = """ select id from pos_order where id = %d"""%(obj.id)
        self.cr.execute(sql)
        if self.cr.fetchone():
            self.cr.execute ("select pol.id,pt.name,pp.default_code as code,pol.qty,pu.name as uom,pol.discount,pol.discount_fixed,pol.price_unit, " \
                                 "(pol.price_unit * pol.qty) as total  " \
                                 "from pos_order as po,pos_order_line as pol,product_product as pp,product_template as pt, product_uom as pu " \
                                 "where pt.id=pp.product_tmpl_id and pp.id=pol.product_id and po.id = pol.order_id  and pu.id=pt.uom_id " \
                                 "and po.state IN ('paid','invoiced') and to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date = current_date and po.id=%d"%(obj.id))
            data = self.cr.dictfetchall()

        else:
            self.cr.execute ("select pt.name,pp.default_code as code,pol.qty,pu.name as uom,pol.discount,pol.discount_fixed,pol.price_unit, " \
                                 "(pol.price_unit * pol.qty) as total  " \
                                 "from pos_order as po,pos_order_line as pol,product_product as pp,product_template as pt, product_uom as pu  " \
                                 "where pt.id=pp.product_tmpl_id and pp.id=pol.product_id and po.id = pol.order_id and pu.id=pt.uom_id  " \
                                 "and po.state IN ('paid','invoiced') and to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date = current_date")
            data = self.cr.dictfetchall()

        for d in data:
            if d['discount_fixed'] != 0:
                d['total'] = d['price_unit'] * d['qty'] - d['discount_fixed']
            else:
                d['total'] = d['price_unit'] * d['qty'] * (1 - (d['discount'] / 100))

        self.total = obj.amount_total
        self.discount_total += obj.discount_total
        self.discount_percent += obj.discount_percent
        return data

    def _pos_payment_total(self, o):
        return self.total

    def _pos_fixed_discount(self, o):
        return self.discount_total

    def _pos_percent_discount(self, o):
        return self.discount_percent


class report_pos_payment(osv.AbstractModel):
    _name = 'report.discounts_in_pos.report_payment'
    _inherit = 'report.abstract_report'
    _template = 'discounts_in_pos.report_payment'
    _wrapped_report_class = pos_payment_report_new
