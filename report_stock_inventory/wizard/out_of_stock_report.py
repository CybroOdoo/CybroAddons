# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (
#    OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import json
import io
import xlsxwriter
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import json_default


class OutOfStockReport(models.TransientModel):
    _name = "stock.out.of.stock.report"
    _description = "Out of Stock Report"

    category_id = fields.Many2one('product.category', string='Product Category')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def _get_out_of_stock_query_and_params(self):
        lang = self.env.context.get('lang', 'en_US')
        query = """
            SELECT 
                COALESCE(pt.name->>%s, pt.name->>'en_US', pt.name::text) AS product_name,
                pp.default_code,
                pc.complete_name as category_name,
                COALESCE(SUM(sq.quantity), 0) AS total_quantity,
                rc.name as company_name
            FROM product_product pp
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN product_category pc ON pt.categ_id = pc.id
            LEFT JOIN res_company rc ON pt.company_id = rc.id
            LEFT JOIN stock_quant sq ON sq.product_id = pp.id 
                AND sq.location_id IN (SELECT id FROM stock_location WHERE usage = 'internal')
                {quant_company}
            WHERE pt.is_storable = true {filters}
            GROUP BY pp.id, pt.name, pp.default_code, pc.complete_name, rc.name
            HAVING COALESCE(SUM(sq.quantity), 0) <= 0
            ORDER BY pt.name ASC
        """
        params = [lang]
        quant_company = ""
        filters = ""
        
        if self.company_id:
            quant_company = "AND sq.company_id = %s"
            params.append(self.company_id.id)
            
        if self.category_id:
            filters += """ AND pt.categ_id IN (
                WITH RECURSIVE CategoryHierarchy AS (
                    SELECT id FROM product_category WHERE id = %s
                    UNION ALL 
                    SELECT c.id FROM product_category c 
                    JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                ) SELECT id FROM CategoryHierarchy
            )"""
            params.append(self.category_id.id)
            
        if self.company_id:
            filters += " AND (pt.company_id = %s OR pt.company_id IS NULL)"
            params.append(self.company_id.id)
            
        return query.format(quant_company=quant_company, filters=filters), params

    def _get_out_of_stock_data(self):
        """ Internal method to fetch out-of-stock records and validate non-emptiness. """
        query, params = self._get_out_of_stock_query_and_params()
        self.env.cr.execute(query, params)
        out_of_stock_data = self.env.cr.dictfetchall()

        if not out_of_stock_data:
            raise UserError(_("No data found for the selected criteria."))

        return out_of_stock_data

    def action_print_pdf_report(self):
        out_of_stock_data = self._get_out_of_stock_data()

        data = {
            'out_of_stock_data': out_of_stock_data,
            'company_name': self.company_id.name if self.company_id else 'All Companies',
            'category_name': self.category_id.name if self.category_id else 'All Categories',
        }
        return self.env.ref('report_stock_inventory.stock_out_of_stock_report').report_action(self.ids, data=data)

    def action_print_xls_report(self):
        out_of_stock_data = self._get_out_of_stock_data()

        data = {
            'out_of_stock_data': out_of_stock_data,
            'company_name': self.company_id.name if self.company_id else 'All Companies',
            'category_name': self.category_id.name if self.category_id else 'All Categories',
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.out.of.stock.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data, default=json_default),
                     'report_name': 'Out of Stock Report'}}

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        sub_head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12px'})
        txt_center = workbook.add_format({'align': 'center'})
        
        sheet.merge_range('A1:E2', 'OUT OF STOCK REPORT', head)
        sheet.merge_range('A3:E3', data.get('company_name', ''), txt_center)
        if data.get('category_name') != 'All Categories':
            sheet.merge_range('A4:E4', f"Category: {data.get('category_name', '')}", txt_center)
            row_start = 5
        else:
            row_start = 4
            
        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 30)
        
        sheet.write(row_start, 0, 'Sl No', sub_head)
        sheet.write(row_start, 1, 'Product Name', sub_head)
        sheet.write(row_start, 2, 'Product Category', sub_head)
        sheet.write(row_start, 3, 'Reference', sub_head)
        sheet.write(row_start, 4, 'Company Name', sub_head)
        
        sl_no = 1
        row = row_start + 1
        records = data.get('out_of_stock_data', [])
        for record in records:
            sheet.write(row, 0, sl_no, txt_center)
            sheet.write(row, 1, record.get('product_name') or '', txt_center)
            sheet.write(row, 2, record.get('category_name') or '', txt_center)
            sheet.write(row, 3, record.get('default_code') or '', txt_center)
            sheet.write(row, 4, record.get('company_name') or data.get('company_name', ''), txt_center)
            row += 1
            sl_no += 1
            
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
