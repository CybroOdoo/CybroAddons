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


class StockTransferReport(models.TransientModel):
    """ Wizard to get the stock transfer reports. We can get both PDF and
        Excel reports """
    _name = "stock.transfer.report"
    _description = "Stock Transfer Report"

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='To pick the product'
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        help='Pick stock location'
    )
    product_category_id = fields.Many2one(
        'product.category',
        required=True,
        string='Product Category',
        help='To pick product_category'
    )
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string="Operation Type",
        help='To select the operation type'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer/Vendor',
        help='To pick the vendor/customer'
    )
    from_date = fields.Datetime(
        string="Date from",
        help='Stock move start from',
        required=True,
        default=lambda self: fields.Datetime.now() - timedelta(days=30)
    )
    to_date = fields.Datetime(
        string='To date',
        help='Stock move end',
        required=True,
        default=fields.Datetime.now
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company Name',
        default=lambda self: self.env.company,
        help='To pick company'
    )

    @api.constrains("from_date", "to_date")
    def _check_dates(self):
        """Check if from date is less than or equal to to date."""
        for record in self:
            if record.from_date and record.to_date and record.from_date > record.to_date:
                raise ValidationError(_("The 'Date from' must be smaller than or equal to the 'To date'."))

    def _fetch_stock_transfer_rows(self):
        """Fetch stock transfer data using Odoo ORM based on active filters."""
        domain = [('picking_id', '!=', False)]

        # Category filter (hierarchical child_of)
        if self.product_category_id:
            domain.append(('product_id.categ_id', 'child_of', self.product_category_id.id))

        # Product filter
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))

        # Location filter
        if self.location_id:
            domain.append(('location_id', '=', self.location_id.id))

        # Operation Type filter
        if self.picking_type_id:
            domain.append(('picking_id.picking_type_id', '=', self.picking_type_id.id))

        # Partner filter
        if self.partner_id:
            domain.append(('picking_id.partner_id', '=', self.partner_id.id))

        # Company filter
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))

        # Date range filters on picking_id.scheduled_date
        if self.from_date:
            domain.append(('picking_id.scheduled_date', '>=', self.from_date))
        if self.to_date:
            domain.append(('picking_id.scheduled_date', '<=', self.to_date))

        # Perform the search
        moves = self.env['stock.move'].sudo().search(domain, order='picking_id, id')

        rows = []
        for move in moves:
            picking = move.picking_id
            product = move.product_id
            location = move.location_id
            picking_type = picking.picking_type_id
            company = move.company_id or picking.company_id or self.env.company

            rows.append({
                'picking_name': picking.name or '',
                'product_name': product.name or '',
                'scheduled_date': picking.scheduled_date or None,
                'date_deadline': picking.date_deadline or None,
                'date_done': picking.date_done or None,
                'origin': picking.origin or '',
                'complete_name': location.complete_name or location.name or '',
                'display_name': picking_type.display_name or picking_type.name or '',
                'company_name': company.name or '',
                'state': picking.state or 'draft',
            })
        return rows

    def action_print_pdf_report(self):
        """ Function to print PDF report. Values passed to the QWeb template """
        self._check_dates()
        state = {
            'draft': 'Draft',
            'waiting': 'Waiting Another Operation',
            'confirmed': 'Waiting',
            'assigned': 'Ready',
            'done': 'Done',
            'cancel': 'Cancelled'
        }
        stock_picking = self._fetch_stock_transfer_rows()
        company = self.company_id or self.env.company
        data = {
            'product_name': self.product_id.product_tmpl_id.name or '' if self.product_id else '',
            'location': self.location_id.complete_name or '' if self.location_id else '',
            'Product Category': self.product_category_id.display_name or '',
            'company_name': company.name or '',
            'company_street': company.street or '',
            'state': company.state_id.name or '',
            'country': company.country_id.name or '',
            'company_email': company.email or '',
            'stock_picking': stock_picking,
            'status': state
        }
        return self.env.ref(
            'report_stock_inventory.stock_transfer_report').report_action(
            None, data=data)

    def action_print_xls_report(self):
        """ Function to pass data to the Excel file """
        self._check_dates()
        stock_picking = self._fetch_stock_transfer_rows()
        company = self.company_id or self.env.company
        data = {
            'product_name': self.product_id.product_tmpl_id.name or '' if self.product_id else '',
            'location': self.location_id.complete_name or '' if self.location_id else '',
            'Product Category': self.product_category_id.display_name or '',
            'company_name': company.name or '',
            'company_street': company.street or '',
            'state': company.state_id.name or '',
            'country': company.country_id.name or '',
            'company_email': company.email or '',
            'stock_picking': stock_picking,
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': 'stock.transfer.report',
                'output_format': 'xlsx',
                'options': json.dumps(data, default=str),
                'report_name': 'Stock Transfer Report'
            }
        }

    def get_xlsx_report(self, data, response):
        """ Function to print excel file. Customizing Excel file and
            adding data
            :param data :Dictionary contains data
            :param response : Response from the controller"""
        state = {
            'draft': 'Draft',
            'waiting': 'Waiting Another Operation',
            'confirmed': 'Waiting',
            'assigned': 'Ready',
            'done': 'Done',
            'cancel': 'Cancelled'
        }
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
        sheet.write('D8', 'scheduled Date', txt)
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
            sheet.write(row, 1, record.get('picking_name', ''), txt)
            sheet.write(row, 2, record.get('product_name', ''), txt)
            sheet.write(row, 3, record.get('scheduled_date', ''), txt)
            sheet.write(row, 4, record.get('date_deadline', ''), txt)
            sheet.write(row, 5, record.get('date_done', ''), txt)
            sheet.write(row, 6, record.get('origin', ''), txt)
            sheet.write(row, 7, record.get('complete_name', ''), txt)
            sheet.write(row, 8, record.get('display_name', ''), txt)
            sheet.write(row, 9, record.get('company_name', ''), txt)
            sheet.write(row, 10, state.get(record.get('state', 'draft'), 'Draft'), txt)
            flag += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
