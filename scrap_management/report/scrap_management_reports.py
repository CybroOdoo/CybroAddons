# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models


class ScrapManagementReport(models.AbstractModel):
    """To generate report based on query and get report values"""
    _name = "report.scrap_management.report_scrap_order"

    @api.model
    def _get_report_values(self, docids, data=None):
        """ To get the report values based on the user giving conditions"""
        value = self.query_data(data['from_date'], data['to_date'],
                                data['product_id'])
        return {
            'var': value
        }

    def query_data(self, from_date, to_date, product_id):
        """ To fetch values from database using query"""
        query = """select product_template.name as product,
        stock_scrap.scrap_qty as quantity,DATE(stock_scrap.date_done) as 
        date from stock_scrap inner join product_product on 
        stock_scrap.product_id = product_product.id inner join 
        product_template on product_template.id = 
        product_product.product_tmpl_id where stock_scrap.state='done'"""
        if product_id:
            query += """ and product_template.id=%(product_id)s"""
        if from_date:
            query += """ and  DATE(stock_scrap.date_done) >= %(from_date)s"""
        if to_date:
            query += """ and  DATE(stock_scrap.date_done) <= %(to_date)s"""
        self.env.cr.execute(query,
                            {'from_date': from_date,
                             'to_date': to_date,
                             'product_id': product_id,
                             })
        return self.env.cr.dictfetchall()
