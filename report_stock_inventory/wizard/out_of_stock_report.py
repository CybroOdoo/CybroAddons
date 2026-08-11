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
from odoo import fields, models


class OutOfStockReport(models.TransientModel):
    """Transient model to generate Out of Stock Report."""
    _name = "out.of.stock.report"
    _description = "Out of Stock Report"

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='To pick the product'
    )
    product_category_id = fields.Many2one(
        'product.category',
        string='Product Category',
        help='To pick product_category'
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company Name",
        help="Filter data based on company"
    )

    def _fetch_out_of_stock_products(self):
        """Fetch out of stock products for the selected filters.
        Returns:
            list[dict]: List of dictionaries containing product stock info.
        """
        if self.company_id:
            companies = self.company_id
        else:
            companies = self.env.companies

        domain = [
            ("is_storable", "=", True),
        ]
        if self.product_id:
            domain.append(("id", "=", self.product_id.id))
        if self.product_category_id:
            domain.append(("categ_id", "child_of", self.product_category_id.id))
        if self.company_id:
            domain.append(("company_id", "in", [self.company_id.id, False]))

        products = self.env["product.product"].sudo().search(domain)

        rows = []
        for company in companies:
            # Get quantities for these products in the current company from stock.quant
            quants = self.env['stock.quant'].sudo().read_group(
                domain=[
                    ('product_id', 'in', products.ids),
                    ('location_id.usage', '=', 'internal'),
                    ('company_id', '=', company.id)
                ],
                fields=['product_id', 'quantity:sum'],
                groupby=['product_id']
            )

            quant_qty = {q['product_id'][0]: q['quantity'] for q in quants if q['product_id']}

            for product in products:
                # If a product belongs to a specific company, only evaluate it in that company
                if product.company_id and product.company_id.id != company.id:
                    continue

                qty = quant_qty.get(product.id, 0.0)
                if qty <= 0.0:
                    rows.append({
                        'name': product.name,
                        'complete_name': product.categ_id.complete_name or '',
                        'default_code': product.default_code or '',
                        'company_name': company.name,
                    })
        return rows

    def action_print_pdf_report(self):
        """Generate the Out of Stock PDF report."""
        company = self.company_id or self.env.company
        product_stock = self._fetch_out_of_stock_products()
        data = {
            'product_name': self.product_id.display_name or '',
            'company_name': company.name or '',
            'company_street': company.street or '',
            'state': company.state_id.name or '',
            'country': company.country_id.name or '',
            'company_email': company.email or '',
            'product_stock': product_stock
        }
        return self.env.ref(
            'report_stock_inventory.out_of_stock_report').report_action(
            None, data=data)

    def action_print_xls_report(self):
        """ Function to pass data to the Excel file"""
        company = self.company_id or self.env.company
        product_stock = self._fetch_out_of_stock_products()
        data = {
            'product_name': self.product_id.display_name or '',
            'company_name': company.name or '',
            'company_street': company.street or '',
            'state': company.state_id.name or '',
            'country': company.country_id.name or '',
            'company_email': company.email or '',
            'product_stock': product_stock
        }
        json_payload = json.dumps(data, default=str)
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'out.of.stock.report',
                     'output_format': 'xlsx',
                     'options': json_payload,
                     'report_name': 'Out of Stock Report'}}

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
        sheet.merge_range('C2:E3', 'OUT OF STOCK REPORT', head)
        sheet.merge_range('C4:E4', data.get('company_name', ''), txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Product Name', txt)
        sheet.write('C8', 'Product Category', txt)
        sheet.write('D8', 'Reference', txt)
        sheet.write('E8', 'Company Name', txt)
        records = data.get('product_stock', [])
        row = 9
        flag = 1
        rows_written = 0
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record.get('name', ''), txt)
            sheet.write(row, 2, record.get('complete_name', ''), txt)
            sheet.write(row, 3, record.get('default_code', ''), txt)
            sheet.write(row, 4, record.get('company_name', ''), txt)
            flag += 1
            row += 1
            rows_written += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
