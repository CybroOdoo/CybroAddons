# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sumith Sivan(<https://www.cybrosys.com>)
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
################################################################################
"""Model to get the report values"""
from odoo import api, models
from odoo.exceptions import ValidationError


class InventoryReport(models.AbstractModel):
    _name = "report.inventory_valuation_report.report_inventory_valuation"
    _description = "Model to print the pdf report of the inventory Valuation"

    @api.model
    def _get_report_values(self, doc_ids, data):
        """
               Prepare the values for the inventory valuation PDF report.
               :param docids: the IDs of the records that will be used to generate the report.
               :type docids: list
               :param data: the data used to filter the records that will be displayed in the report.
               :type data: dict
               :return: a dictionary containing the report data.
               :rtype: dict
               :raise: ValidationError if no data is found that matches the specified filters.
               This method prepares the data that will be used to generate the inventory valuation PDF report.
               It takes a list of document IDs and a dictionary of filters as input, and returns a dictionary
               containing the data that will be displayed in the report."""
        product_id = []

        query = """select product_product.id as product_id,product_template.default_code as default_code ,
            product_template.name->>'en_US' as name, product_category.name as category from product_template join 
            product_product on product_product.product_tmpl_id = product_template.id join product_category on 
            product_template.categ_id = product_category.id"""

        def get_data(res):
            val_sum = 0
            for rec in res:
                product_id.append(rec['product_id'])

            for i in range(len(res)):
                product = self.env['product.product'].browse(product_id[i])

                purchase_count = self.env['purchase.order.line'].search(
                    [('product_id', '=', product_id[i])])
                valuation = self.env['stock.valuation.layer'].search(
                    [('product_id', '=', product_id[i])],
                    order="create_date desc", limit=1)
                internal_locations = self.env['stock.location'].search(
                    [('usage', '=', 'internal')])
                internal_qty = 0
                for quant in internal_locations:
                    stock_quant = self.env['stock.quant'].search(
                        [('location_id', '=', quant.id),
                         ('product_id', '=', product_id[i])]
                    )

                    if product.tracking == 'lot':
                        lot_qty_count = sum(
                            qty.available_quantity for qty in
                            stock_quant.mapped(
                                'lot_id.quant_ids'))
                        internal_qty += lot_qty_count
                    else:
                        internal_qty += sum(
                            stock_quant.mapped('available_quantity'))

                adjustment_rec = self.env['stock.quant'].search(
                    [('product_id', '=', product_id[i])],
                    order="create_date desc", limit=1)
                adjustment = adjustment_rec.inventory_diff_quantity
                res[i][
                    'costing_method'] = product.categ_id.property_cost_method
                res[i]['standard_price'] = product.standard_price
                res[i]['sale_qty'] = product.sales_count
                res[i]['received_qty'] = sum(
                    purchase_count.mapped('product_uom_qty'))
                res[i]['beginning'] = res[i]['received_qty'] - res[i][
                    'sale_qty']
                res[i]['valuation'] = valuation.value

                res[i]['internal'] = internal_qty
                res[i]['adjustment'] = adjustment
                val_sum += valuation.value
                res[i]['valuation_sum'] = val_sum

            return res

        if data['my_company_id']:
            new_query = f""" join res_company on res_company.id=product_template.company_id where res_company.id='{data['my_company_id']}'"""
            query += new_query

        if data['from_date']:
            new_query = f""" and product_product.create_date >= '{data['from_date']}'"""
            query += new_query

        if data['end_date']:
            new_query = f""" and product_product.create_date <= '{data['end_date']}'"""
            query += new_query

        product = tuple(data['products'])
        categories = tuple(data['categories'])

        if data['filter_by'] == 'product':
            if len(product) == 1:
                new_query = f""" and product_product.id = {product[0]} """
                query += new_query
            elif len(product) > 1:
                new_query = f""" and product_product.id in {product} """
                query += new_query
            else:
                raise ValidationError('No Product Found')
        elif data['filter_by'] == 'category':
            if data['categories']:
                if len(categories) == 1:
                    new_query = f""" and product_category.id = {categories[0]}"""
                    query += new_query
            elif len(categories) > 1:
                new_query = f""" and product_category.id in {categories} """
                query += new_query
            else:
                raise ValidationError('No Category Found')

        self.env.cr.execute(query)
        record = self.env.cr.dictfetchall()
        if len(record) > 0:
            result = get_data(record)
            return {
                'data': data,
                'company': self.env.company,
                'result': result,
            }
        else:
            raise ValidationError('No Data Found !')
