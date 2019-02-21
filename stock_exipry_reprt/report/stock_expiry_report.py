# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import ValidationError, Warning


class CustomReport(models.TransientModel):
    _name = "report.stock_exipry_reprt.stock_expiry_reports"

    def _get_report_values(self,docids,data=None):
        cr = self._cr
        query = """SELECT spl.name,spl.life_date,spl.product_id,pt.name as product_name ,sl.complete_name as location_name,sl.id as location_id
        from stock_production_lot spl
        join product_product as pp
        on spl.product_id = pp.id 
        join product_template pt
        on pp.product_tmpl_id = pt.id
        join stock_quant sq
        on pp.id = sq.product_id
        join stock_location sl
        on sq.location_id = sl.id
        where usage != 'view' and (spl.life_date::DATE-now()::date) > %s"""
        cr.execute(query, [data['report_dayz']])
        dat = cr.dictfetchall()
        count = 0
        if data['check']:
            if data['int_location']:
                for val in dat:
                    if data['int_location'] == val['location_id']:
                        count = 1
                        break
                new_list = []
                if count == 1:
                    for item in dat:
                        if item['location_id'] == data['int_location']:
                            new_list.append(item)
                    dat = new_list
            else:
                count = 1
        if not data['int_location']:
            count = 1
        if count == 0:
            raise ValidationError(_("No Products Expired In the Selected Location"))
        if not dat:
            raise Warning('No Products Are Expired In These Days')
        return {
            'doc_ids': self.ids,
            'doc_model': 'stockz.expiry',
            'dat': dat,
            'data': data,
        }
