# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Linto C T(<https://www.cybrosys.com>)
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

from odoo import models, api
from datetime import datetime


class ReportAvgPrices(models.AbstractModel):
    _name = 'report.product_ageing_report.report_ageing_analysis'

    def get_productss(self, docs):
        """input : starting date, location and category
          output: a dictionary with all the products and their stock for that currespnding intervals"""

        cr = self._cr
        if docs.location_id and docs.product_categ:
            cr.execute("select sq.id from stock_quant sq inner join product_product pp on(pp.id=sq.product_id) "
                       " inner join product_template pt on(pt.id=pp.product_tmpl_id and pt.categ_id in %s) "
                       "where sq.location_id in %s and sq.qty > 0 and sq.in_date <=%s", (tuple(docs.product_categ.ids),
                                                                     tuple(docs.location_id.ids), docs.from_date))
        elif docs.location_id:
            cr.execute("select sq.id from stock_quant sq where sq.location_id in %s and sq.qty > 0 and sq.in_date <=%s",
                       (tuple(docs.location_id.ids), docs.from_date))
        elif docs.product_categ:
            cr.execute("select sq.id from stock_quant sq inner join product_product pp on(pp.id=sq.product_id) "
                       " inner join product_template pt on(pt.id=pp.product_tmpl_id and pt.categ_id in %s)"
                       "where sq.qty > 0  and sq.in_date <=%s", (tuple(docs.product_categ.ids), docs.from_date))
        else:
            cr.execute("select id from stock_quant where qty > 0  and in_date <=%s", (docs.from_date,))
        quant_ids = cr.fetchall()
        quant_id = []
        for i in quant_ids:
            quant_id.append(i[0])
        rec = self.env['stock.quant'].browse(quant_id)
        products = {}
        product_list = []
        for i in rec:
            date1 = datetime.strptime(docs.from_date, '%Y-%m-%d %H:%M:%S').date()
            if len(i.history_ids) == 1 and i.product_id.id not in product_list:
                product_list.append(i.product_id.id)
                temp = {
                    'product': i.product_id.name,
                    'total_qty': i.qty,
                }
                qty = [0, 0, 0, 0, 0]

                date2 = datetime.strptime(i.in_date, '%Y-%m-%d %H:%M:%S').date()
                no_days = (date1 - date2).days
                t1 = 0
                t2 = docs.interval
                for j in range(0, 5):
                    if no_days >= 4 * docs.interval:
                        qty[4] += i.qty
                        break
                    elif no_days in range(t1, t2):
                        qty[j] += i.qty
                        break

                    t1 = t2
                    t2 += docs.interval
                temp['qty'] = qty
                products[i.product_id.id] = temp
            elif len(i.history_ids) == 1 and i.product_id.id in product_list:
                date2 = datetime.strptime(i.in_date, '%Y-%m-%d %H:%M:%S').date()
                no_days = (date1 - date2).days
                t1 = 0
                t2 = docs.interval
                for j in range(0, 5):
                    if no_days >= 4 * docs.interval:
                        products[i.product_id.id]['qty'][4] += i.qty
                        products[i.product_id.id]['total_qty'] += i.qty
                        break
                    elif no_days in range(t1, t2):
                        products[i.product_id.id]['qty'][j] += i.qty
                        products[i.product_id.id]['total_qty'] += i.qty
                        break

                    t1 = t2
                    t2 += docs.interval
        return products

    @api.model
    def render_html(self, docids, data=None):
        """we are overwriting this function because we need to show values from other models in the report
                we pass the objects in the docargs dictionary"""

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        products = self.get_productss(docs)
        interval = ['0-'+str(docs.interval),
                    str(docs.interval)+'-'+str(2*docs.interval),
                    str(2*docs.interval)+'-'+str(3*docs.interval),
                    str(3*docs.interval)+'-'+str(4*docs.interval),
                    str(4*docs.interval)+'+']
        loc = ""
        categ = ""
        for i in docs.location_id:
            if i.location_id.name and i.name:
                loc += i.location_id.name+" / "+i.name+", "
        for i in docs.product_categ:
            if i.name:
                categ += i.name+", "
        loc = loc[:-2]
        categ = categ[:-2]
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'loc': loc,
            'categ': categ,
            'interval': interval,
            'products': products,
        }
        return self.env['report'].render('product_ageing_report.report_ageing_analysis', docargs)
