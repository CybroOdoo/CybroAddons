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
import io
import json
import xlsxwriter
from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import json_default


class StockTransferReport(models.TransientModel):
    """ Wizard to getting the stock transfer reports in PDF and Excel format. """
    _name = "stock.transfer.report"
    _description = "Stock Transfer Report"

    product_id = fields.Many2one('product.product', string='Product',
                                 help='To pick the product')
    location_id = fields.Many2one('stock.location', string='Location',
                                  help='Pick stock location')
    product_category_id = fields.Many2one('product.category', required=True,
                                          string='Product Category',
                                          help='To pick product_category')
    picking_type_id = fields.Many2one('stock.picking.type',
                                      string="Operation Type",
                                      help='To select the operation type')
    partner_id = fields.Many2one('res.partner', string='Customer/Vendor',
                                 help='To pick the vendor/customer')
    from_date = fields.Datetime(string="Date from",
                                help='Stock move start from',
                                required=True, default=fields.Datetime.now())
    to_date = fields.Datetime(string='To date', help='Stock move end',
                              required=True, default=fields.Datetime.now())
    company_id = fields.Many2one('res.company', string='Company Name',
                                 default=lambda self: self.env.company,
                                 help='To pick company')

    def _get_stock_transfer_data(self):
        """ Fetch stock transfer data based on wizard filters. """
        if self.from_date and self.to_date and self.to_date < self.from_date:
            raise ValidationError(_("To Date must be greater than or equal to Date From..."))

        lang = self.env.context.get('lang', 'en_US')
        query = """WITH RECURSIVE CategoryHierarchy AS (
                        SELECT id, name, parent_id FROM product_category WHERE id = %s 
                        UNION ALL 
                        SELECT c.id, c.name, c.parent_id FROM product_category c 
                        JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                    ) 
                    SELECT 
                        CategoryHierarchy.id as category_id, 
                        CategoryHierarchy.name as category_name, 
                        stock_picking.name as picking_name,
                        COALESCE(product_template.name->>%s, product_template.name->>'en_US', product_template.name::text) as product_name,
                        stock_picking.scheduled_date, 
                        stock_picking.date_deadline,
                        stock_picking.date_done, 
                        stock_picking.origin,
                        stock_location.complete_name,
                        stock_picking_type.display_name,
                        res_company.name as company_name,
                        stock_picking.state 
                    FROM CategoryHierarchy
                    JOIN product_category on CategoryHierarchy.id = product_category.id 
                    JOIN product_template on product_category.id = product_template.categ_id
                    JOIN product_product on product_template.id = product_product.product_tmpl_id 
                    JOIN stock_move on product_product.id = stock_move.product_id
                    JOIN stock_picking on stock_move.picking_id = stock_picking.id 
                    JOIN stock_picking_type on stock_picking.picking_type_id = stock_picking_type.id
                    JOIN res_company on stock_picking.company_id = res_company.id 
                    JOIN stock_location on stock_move.location_id = stock_location.id
                    WHERE 1=1
                """
        params = [self.product_category_id.id, lang]

        if self.product_id:
            query += " AND product_product.id = %s"
            params.append(self.product_id.id)
        if self.location_id:
            query += " AND stock_move.location_id = %s"
            params.append(self.location_id.id)
        if self.picking_type_id:
            query += " AND stock_picking.picking_type_id = %s"
            params.append(self.picking_type_id.id)
        if self.partner_id:
            query += " AND stock_picking.partner_id = %s"
            params.append(self.partner_id.id)
        if self.company_id:
            query += " AND stock_picking.company_id = %s"
            params.append(self.company_id.id)
        if self.from_date:
            query += " AND stock_picking.scheduled_date >= %s"
            params.append(self.from_date)
        if self.to_date:
            query += " AND stock_picking.scheduled_date <= %s"
            params.append(self.to_date)

        query += " ORDER BY stock_picking.scheduled_date DESC"

        self.env.cr.execute(query, params)
        stock_picking = self.env.cr.dictfetchall()

        if not stock_picking:
            raise UserError(_("No data found for the selected criteria."))

        return stock_picking

    def action_print_pdf_report(self):
        """ Function to print pdf report. Value passed to the pdf template."""
        state = {'draft': 'Draft', 'waiting': 'Waiting Another Operation',
                 'confirmed': 'Waiting', 'assigned': 'Ready', 'done': 'Done',
                 'cancel': 'Cancelled'}
        stock_picking = self._get_stock_transfer_data()
        data = {
            'product_name': self.product_id.product_tmpl_id.name if self.product_id else '',
            'location': self.location_id.complete_name if self.location_id else '',
            'Product Category': self.product_category_id.display_name,
            'company_name': self.company_id.name if self.company_id else '',
            'company_street': self.company_id.street if self.company_id else '',
            'state': self.company_id.state_id.name if self.company_id and self.company_id.state_id else '',
            'country': self.company_id.country_id.name if self.company_id and self.company_id.country_id else '',
            'company_email': self.company_id.email if self.company_id else '',
            'stock_picking': stock_picking,
            'status': state
        }
        return self.env.ref(
            'report_stock_inventory.stock_transfer_report').report_action(
            self.ids, data=data)

    def action_print_xls_report(self):
        """ Function to pass data to the Excel file."""
        stock_picking = self._get_stock_transfer_data()
        data = {
            'product_name': self.product_id.product_tmpl_id.name if self.product_id else '',
            'location': self.location_id.complete_name if self.location_id else '',
            'Product Category': self.product_category_id.display_name,
            'company_name': self.company_id.name if self.company_id else '',
            'company_street': self.company_id.street if self.company_id else '',
            'state': self.company_id.state_id.name if self.company_id and self.company_id.state_id else '',
            'country': self.company_id.country_id.name if self.company_id and self.company_id.country_id else '',
            'company_email': self.company_id.email if self.company_id else '',
            'stock_picking': stock_picking,
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.transfer.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=json_default),
                     'report_name': 'Stock Transfer Report'}}

    def get_xlsx_report(self, data, response):
        """ Function to print excel file. Customizing Excel file and adding data
            :param data :Dictionary contains results
            :param response : Response from the controller"""
        state = {'draft': 'Draft', 'waiting': 'Waiting Another Operation',
                 'confirmed': 'Waiting', 'assigned': 'Ready', 'done': 'Done',
                 'cancel': 'Cancelled'}
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column(0, 10, 24)
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'align': 'center'})
        sheet.merge_range('B2:I3', 'STOCK TRANSFER REPORT', head)
        sheet.merge_range('D4:F4', data.get('company_name', ''), txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Reference', txt)
        sheet.write('C8', 'Product', txt)
        sheet.write('D8', 'Scheduled Date', txt)
        sheet.write('E8', 'Deadline', txt)
        sheet.write('F8', 'Effective Date', txt)
        sheet.write('G8', 'Source Document', txt)
        sheet.write('H8', 'Location', txt)
        sheet.write('I8', 'Operation Type', txt)
        sheet.write('J8', 'Company Name', txt)
        sheet.write('K8', 'Status', txt)
        records = data.get('stock_picking', [])
        row = 9
        flag = 1
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record.get('picking_name') or '', txt)
            sheet.write(row, 2, record.get('product_name') or '', txt)
            sheet.write(row, 3, str(record['scheduled_date']) if record.get('scheduled_date') else '', txt)
            sheet.write(row, 4, str(record['date_deadline']) if record.get('date_deadline') else '', txt)
            sheet.write(row, 5, str(record['date_done']) if record.get('date_done') else '', txt)
            sheet.write(row, 6, record.get('origin') or '', txt)
            sheet.write(row, 7, record.get('complete_name') or '', txt)
            sheet.write(row, 8, record.get('display_name') or '', txt)
            sheet.write(row, 9, record.get('company_name') or '', txt)
            sheet.write(row, 10, state.get(record.get('state'), record.get('state') or ''), txt)
            flag += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
