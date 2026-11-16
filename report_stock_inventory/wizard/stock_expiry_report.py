# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
#    For full details, see https://www.odoo.com/documentation/20.0/legal/licenses/licenses.html
#
#############################################################################
import io
import json
import xlsxwriter
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockExpiryReport(models.TransientModel):
    """ Models helps to print excel and pdf report of expired stock
        items based on expiry field"""
    _name = "stock.expiry.report"
    _description = "Stock Expiry Report"

    product_id = fields.Many2one(
        'product.product',
        help='To pick the product'
    )
    product_category_id = fields.Many2one(
        'product.category',
        required=True,
        help='To pick product_category'
    )
    from_date = fields.Datetime(
        required=True,
        default=lambda self: fields.Datetime.now() - timedelta(days=30),
        help='For filtering data using from date'
    )
    to_date = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        help='For filtering data using to date'
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company
    )

    @api.constrains("from_date", "to_date")
    def _check_dates(self):
        """Check if from date is less than or equal to to date."""
        for record in self:
            if record.from_date and record.to_date and record.from_date > record.to_date:
                raise ValidationError(self.env._("The 'From Date' must be smaller than or equal to the 'To Date'."))

    def _fetch_stock_expiry_rows(self):
        """Fetch stock expiry rows matching the wizard criteria and populate complete_name."""
        self._check_dates()
        lang = self.env.context.get('lang', 'en_US') or 'en_US'
        query = """ WITH RECURSIVE CategoryHierarchy AS (
                    SELECT id, name, parent_id FROM product_category WHERE id = %s
                    UNION ALL
                    SELECT c.id, c.name, c.parent_id FROM product_category c
                    JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                )
                SELECT stock_lot.name as sl_no,
                       CategoryHierarchy.id as category_id,
                       CategoryHierarchy.name as category_name,
                       stock_quant.expiration_date,
                       product_template.name ->>%s as name,
                       MAX(stock_quant.inventory_quantity) as inventory_quantity,
                       res_company.name as company_name,
                       SUM(stock_quant.quantity) as quantity
                FROM CategoryHierarchy
                JOIN product_category ON CategoryHierarchy.id = product_category.id
                JOIN product_template ON product_category.id = product_template.categ_id
                JOIN product_product ON product_template.id = product_product.product_tmpl_id
                JOIN stock_quant ON product_product.id = stock_quant.product_id
                JOIN res_company ON stock_quant.company_id = res_company.id
                JOIN stock_lot ON stock_quant.lot_id = stock_lot.id
                JOIN stock_location ON stock_quant.location_id = stock_location.id
        """
        params = [self.product_category_id.id, lang]
        conditions = [
            "stock_location.usage = 'internal'",
            "stock_quant.expiration_date IS NOT NULL",
        ]
        if self.product_id:
            conditions.append("product_product.id = %s")
            params.append(self.product_id.id)
        if self.company_id:
            conditions.append("stock_quant.company_id = %s")
            params.append(self.company_id.id)
        if self.from_date:
            conditions.append("stock_quant.expiration_date >= %s")
            params.append(self.from_date)
        if self.to_date:
            conditions.append("stock_quant.expiration_date < %s")
            params.append(self.to_date)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        group_by_clause = """ GROUP BY stock_lot.id, stock_lot.name,
                    product_product.id, product_template.name ->>%s,
                    CategoryHierarchy.id, CategoryHierarchy.name,
                    res_company.id, res_company.name,
                    stock_quant.expiration_date
                    HAVING SUM(stock_quant.quantity) > 0
        """
        params.append(lang)
        self.env.cr.execute(query + where_clause + group_by_clause, tuple(params))
        stock_expiry = self.env.cr.dictfetchall()
        if not stock_expiry:
            return []

        # Populate complete_name using product.category ORM as complete_name is a computed field in Odoo 17+
        category_ids = {r['category_id'] for r in stock_expiry if r.get('category_id')}
        categories = self.env['product.category'].browse(category_ids)
        category_names = {c.id: c.complete_name or c.name for c in categories}
        for r in stock_expiry:
            r['complete_name'] = category_names.get(r.get('category_id'), r.get('category_name', ''))
        return stock_expiry

    def action_print_xls_report(self):
        """ Function to pass data to the Excel file"""
        stock_expiry = self._fetch_stock_expiry_rows()
        if not stock_expiry:
            raise ValidationError(self.env._("There is no data to print."))
        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'product_name': self.product_id.product_tmpl_id.name,
            'vehicle_id': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_expiry': stock_expiry,
        }
        json_payload = json.dumps(data, default=str)
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.expiry.report',
                     'output_format': 'xlsx',
                     'options': json_payload,
                     'report_name': 'Stock Expiry Report'}}

    def get_xlsx_report(self, data, response):
        """ Function to print excel report.Customizing Excel file and added data
            :param data :Dictionary contains data
            :param response : Response from the controller"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column(0, 10, 24)
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'align': 'center'})
        sheet.merge_range('C2:E3', 'STOCK EXPIRY REPORT', head)
        sheet.merge_range('C4:E4', data['company_name'], txt)
        sheet.write('F3', 'From Date', txt)
        sheet.write('F4', 'To Date', txt)
        sheet.write('G3', data['from_date'], txt)
        sheet.write('G4', data['to_date'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', ' Expiry Date', txt)
        sheet.write('C8', 'Product Name', txt)
        sheet.write('D8', 'Lot/Sl', txt)
        sheet.write('E8', 'Product Category', txt)
        sheet.write('F8', 'Company Name', txt)
        sheet.write('G8', 'Quantity', txt)
        records = data['stock_expiry']
        row = 9
        flag = 1
        rows_written = 0
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record['expiration_date'], txt)
            sheet.write(row, 2, record['name'], txt)
            sheet.write(row, 3, record['sl_no'], txt)
            sheet.write(row, 4, record['complete_name'], txt)
            sheet.write(row, 5, record['company_name'], txt)
            sheet.write(row, 6, record['quantity'], txt)
            flag += 1
            row += 1
            rows_written += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def action_print_pdf_report(self):
        """ Function to pass data to the PDF report"""
        stock_expiry = self._fetch_stock_expiry_rows()
        if not stock_expiry:
            raise ValidationError(self.env._("There is no data to print."))
        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'product_name': self.product_id.product_tmpl_id.name,
            'vehicle_id': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_expiry': stock_expiry,
        }
        return self.env.ref(
            'report_stock_inventory.stock_expiry_report').report_action(
            None, data=data)
    