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
from datetime import timedelta
from odoo import fields, models, _
from odoo.exceptions import UserError


class StockExpiryReport(models.TransientModel):
    _name = "stock.expiry.report"
    _description = "Stock Expiry Report"

    product_id = fields.Many2one('product.product', string='Product')
    category_id = fields.Many2one('product.category', string='Product Category')
    location_id = fields.Many2one('stock.location', string='Location', domain=[('usage', '=', 'internal')])
    expiry_date = fields.Date(string='Expires Before', required=True, 
                              default=lambda self: fields.Date.today() + timedelta(days=30))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def _get_stock_expiry_data(self):
        """ Internal helper method to query stock expiry data with child category support and validation. """
        lang = self.env.context.get('lang', 'en_US')
        query = """
            SELECT 
                COALESCE(pt.name->>%s, pt.name->>'en_US', pt.name::text) as product_name,
                sl.name as lot_name,
                sl.expiration_date,
                sq.quantity,
                loc.complete_name as location_name,
                rc.name as company_name
            FROM stock_quant sq
            JOIN product_product pp ON sq.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN stock_lot sl ON sq.lot_id = sl.id
            JOIN stock_location loc ON sq.location_id = loc.id
            JOIN res_company rc ON sq.company_id = rc.id
            WHERE sl.expiration_date <= %s
        """
        params = [lang, self.expiry_date]
        
        if self.product_id:
            query += " AND pp.id = %s"
            params.append(self.product_id.id)
        if self.category_id:
            query += """ AND pt.categ_id IN (
                WITH RECURSIVE CategoryHierarchy AS (
                    SELECT id FROM product_category WHERE id = %s
                    UNION ALL 
                    SELECT c.id FROM product_category c 
                    JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                ) SELECT id FROM CategoryHierarchy
            )"""
            params.append(self.category_id.id)
        if self.location_id:
            query += " AND loc.id = %s"
            params.append(self.location_id.id)
        if self.company_id:
            query += " AND sq.company_id = %s"
            params.append(self.company_id.id)

        query += " ORDER BY sl.expiration_date ASC"

        self.env.cr.execute(query, params)
        expiry_data = self.env.cr.dictfetchall()

        if not expiry_data:
            raise UserError(_("No data found for the selected criteria."))

        return expiry_data

    def action_print_pdf_report(self):
        expiry_data = self._get_stock_expiry_data()
        data = {
            'expiry_data': expiry_data,
            'expiry_date': self.expiry_date,
        }
        return self.env.ref('report_stock_inventory.stock_expiry_report').report_action(self.ids, data=data)

    def action_print_xls_report(self):
        expiry_data = self._get_stock_expiry_data()
        data = {
            'expiry_data': expiry_data,
            'expiry_date': str(self.expiry_date),
            'company_name': self.company_id.name if self.company_id else '',
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.expiry.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data, default=str),
                     'report_name': 'Stock Expiry Report'}}

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        sub_head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12px'})
        txt = workbook.add_format({'align': 'left'})
        txt_center = workbook.add_format({'align': 'center'})
        txt_right = workbook.add_format({'align': 'right'})
        
        sheet.merge_range('A1:F2', 'STOCK EXPIRY REPORT', head)
        sheet.merge_range('A3:F3', f"Expires Before: {data.get('expiry_date', '')}", sub_head)
        sheet.merge_range('A4:F4', data.get('company_name', ''), txt_center)
        
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 30)
        sheet.set_column('F:F', 20)
        
        sheet.write('A6', 'Product', sub_head)
        sheet.write('B6', 'Lot/Serial Number', sub_head)
        sheet.write('C6', 'Expiration Date', sub_head)
        sheet.write('D6', 'Quantity', sub_head)
        sheet.write('E6', 'Location', sub_head)
        sheet.write('F6', 'Company', sub_head)
        
        row = 6
        records = data.get('expiry_data', [])
        for record in records:
            sheet.write(row, 0, record.get('product_name') or '', txt)
            sheet.write(row, 1, record.get('lot_name') or '', txt)
            sheet.write(row, 2, str(record['expiration_date']) if record.get('expiration_date') else '', txt_center)
            sheet.write(row, 3, record.get('quantity', 0), txt_right)
            sheet.write(row, 4, record.get('location_name') or '', txt)
            sheet.write(row, 5, record.get('company_name') or '', txt)
            row += 1
            
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
