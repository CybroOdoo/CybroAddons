# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anshad Ahammed M (odoo@cybrosys.com)
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
import io
import json
import xlsxwriter
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockExpiryReport(models.TransientModel):
    """ Models helps to print excel and pdf report of expired stock
        items based on expiry field"""
    _name = "stock.expiry.report"
    _description = "Stock Expiry Report"

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='To pick the product'
    )
    product_category_id = fields.Many2one(
        'product.category',
        string='Product Category',
        required=True,
        help='To pick product_category'
    )
    from_date = fields.Datetime(
        string='From Date',
        required=True,
        default=lambda self: fields.Datetime.now() - timedelta(days=30),
        help='For filtering data using from date'
    )
    to_date = fields.Datetime(
        string='To Date',
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
                raise ValidationError(_("The 'From Date' must be smaller than or equal to the 'To Date'."))

    def action_print_xls_report(self):
        """ Function to pass data to the Excel file"""
        self._check_dates()
        lang = f"'{self.env.context['lang']}'"
        query = """ WITH RECURSIVE CategoryHierarchy AS (SELECT id,name, 
                    parent_id FROM product_category where id = {} UNION ALL 
                    SELECT c.id, c.name, c.parent_id FROM product_category c
                    JOIN CategoryHierarchy ch ON c.parent_id = ch.id)
                    SELECT stock_lot.name as sl_no,CategoryHierarchy.id as category_id,
                    CategoryHierarchy.name as category_name,
                    stock_quant.expiration_date, product_template.name ->>{}
                    as name, MAX(stock_quant.inventory_quantity) as inventory_quantity,
                    product_category.complete_name,res_company.name as 
                    company_name, SUM(stock_quant.quantity) as quantity
                    FROM CategoryHierarchy JOIN product_category on 
                    CategoryHierarchy.id = product_category.id JOIN 
                    product_template on product_category.id = 
                    product_template.categ_id JOIN product_product on 
                    product_template.id = product_product.product_tmpl_id JOIN
                    stock_quant on product_product.id = 
                    stock_quant.product_id JOIN res_company on 
                    stock_quant.company_id = res_company.id join
					stock_lot on stock_quant.lot_id = stock_lot.id join
					stock_location on stock_quant.location_id = stock_location.id
                    """.format(self.product_category_id.id,lang)
        product_id = self.product_id.id
        company_id = self.company_id.id
        from_date = self.from_date
        to_date = self.to_date
        conditions = []
        # Only count quants sitting in real warehouse locations; virtual
        # locations (inventory adjustment, vendors, customers, transit, ...)
        # are ledger-balancing rows, not physical, expirable stock.
        conditions.append("stock_location.usage = 'internal'")
        if self.product_id:
            conditions.append("product_product.id = '{}'".format(product_id))
        if self.company_id:
            conditions.append("stock_quant.company_id = '{}'".format(company_id))
        conditions.append("stock_quant.expiration_date IS NOT NULL")
        if from_date:
            conditions.append("stock_quant.expiration_date >= '{}'".format(from_date))
        if to_date:
            conditions.append("stock_quant.expiration_date < '{}'".format(to_date))

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        # Aggregate per product/lot instead of returning one row per
        # stock.quant, so opposing +/- quant rows (e.g. an internal
        # location vs. a virtual adjustment location) net into a single
        # correct on-hand quantity per lot.
        group_by_clause = """ GROUP BY stock_lot.id, stock_lot.name,
                    product_product.id, product_template.name ->>{},
                    CategoryHierarchy.id, CategoryHierarchy.name,
                    product_category.complete_name, res_company.id,
                    res_company.name, stock_quant.expiration_date
                    HAVING SUM(stock_quant.quantity) > 0
                    """.format(lang)
        final_sql = query + where_clause + group_by_clause
        self.env.cr.execute(final_sql)
        stock_expiry = self.env.cr.dictfetchall()
        data = {
            'from_date' : from_date,
            'to_date' : to_date,
            'product_name': self.product_id.product_tmpl_id.name,
            'vehicle_id': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_expiry': stock_expiry
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
        """ Function to pass data to the Excel file"""
        self._check_dates()
        lang = f"'{self.env.context['lang']}'"
        query = """WITH RECURSIVE CategoryHierarchy AS (SELECT id,name, 
                    parent_id FROM product_category where id = {} UNION ALL 
                    SELECT c.id, c.name, c.parent_id FROM product_category c
                    JOIN CategoryHierarchy ch ON c.parent_id = ch.id)
                    SELECT stock_lot.name as sl_no,CategoryHierarchy.id as category_id,
                    CategoryHierarchy.name as category_name,
                    stock_quant.expiration_date, product_template.name ->>{}
                    as name, MAX(stock_quant.inventory_quantity) as inventory_quantity,
                    product_category.complete_name,res_company.name as 
                    company_name, SUM(stock_quant.quantity) as quantity
                    FROM CategoryHierarchy JOIN product_category on 
                    CategoryHierarchy.id = product_category.id JOIN 
                    product_template on product_category.id = 
                    product_template.categ_id JOIN product_product on 
                    product_template.id = product_product.product_tmpl_id JOIN
                    stock_quant on product_product.id = 
                    stock_quant.product_id JOIN res_company on 
                    stock_quant.company_id = res_company.id join
					stock_lot on stock_quant.lot_id = stock_lot.id join
					stock_location on stock_quant.location_id = stock_location.id
                            """.format(self.product_category_id.id, lang)
        product_id = self.product_id.id
        company_id = self.company_id.id
        from_date = self.from_date
        to_date = self.to_date
        conditions = []
        # Only count quants sitting in real warehouse locations; virtual
        # locations (inventory adjustment, vendors, customers, transit, ...)
        # are ledger-balancing rows, not physical, expirable stock.
        conditions.append("stock_location.usage = 'internal'")
        if self.product_id:
            conditions.append("product_product.id = '{}'".format(product_id))
        if self.company_id:
            conditions.append("stock_quant.company_id = '{}'".format(company_id))
        conditions.append("stock_quant.expiration_date IS NOT NULL")
        if from_date:
            conditions.append("stock_quant.expiration_date >= '{}'".format(from_date))
        if to_date:
            conditions.append("stock_quant.expiration_date < '{}'".format(to_date))

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        # Aggregate per product/lot instead of returning one row per
        # stock.quant, so opposing +/- quant rows (e.g. an internal
        # location vs. a virtual adjustment location) net into a single
        # correct on-hand quantity per lot.
        group_by_clause = """ GROUP BY stock_lot.id, stock_lot.name,
                    product_product.id, product_template.name ->>{},
                    CategoryHierarchy.id, CategoryHierarchy.name,
                    product_category.complete_name, res_company.id,
                    res_company.name, stock_quant.expiration_date
                    HAVING SUM(stock_quant.quantity) > 0
                    """.format(lang)
        self.env.cr.execute(query + where_clause + group_by_clause)
        stock_expiry = self.env.cr.dictfetchall()
        data = {
            'from_date': from_date,
            'to_date': to_date,
            'product_name': self.product_id.product_tmpl_id.name,
            'vehicle_id': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_expiry': stock_expiry
        }
        return self.env.ref(
            'report_stock_inventory.stock_expiry_report').report_action(
            None, data=data)
    