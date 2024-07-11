# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import io
import xlsxwriter
from odoo import fields, models
from odoo.tools import date_utils
import json


class TurnoverReport(models.TransientModel):
    """Wizard created for select date, products, categories, companies and
    warehouses. The records are filtered by using these fields"""
    _name = "turnover.report"
    _description = "Turnover Report"

    start_date = fields.Date(string="Start Date",
                             help="Select inventory start date.")
    end_date = fields.Date(string="End Date",
                           help="Select inventory end date.")
    product_ids = fields.Many2many('product.product',
                                   string="Products",
                                   default=lambda self: self.env[
                                       'product.product'].search([], limit=1),
                                   help="Select multiple products "
                                        "from the list.")
    category_ids = fields.Many2many('product.category',
                                    string="Category",
                                    default=lambda
                                        self: self._default_categ_ids(),
                                    help="Select multiple categories "
                                         "from the list")
    warehouse_ids = fields.Many2many('stock.warehouse',
                                     string="Warehouse",
                                     default=lambda
                                         self: self._default_warehouse_ids(),
                                     help="Select multiple warehouses "
                                          "from the list.")
    company_ids = fields.Many2many('res.company', string="Company",
                                   default=lambda self: self.env.company,
                                   help="Select multiple companies "
                                        "from the list.")

    def _default_categ_ids(self):
        """Return default category to selection field."""
        category = self.env['product.product'].search(
            [], limit=1).product_tmpl_id.categ_id
        return [(6, 0, [category.id])] if category else []

    def _default_warehouse_ids(self):
        """Return default warehouse to selection field."""
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        return [(6, 0, [warehouse.id])] if warehouse else []

    def action_pdf_report_generate(self):
        """Here generate a dictionary of list of datas and that return to a
        report action. And it will generate the pdf report. """
        data = {
            'stock_report': self.call_render_report(),
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        return (self.env.ref(
            'inventory_turnover_report_analysis.inventory_turnover_report').
                report_action(self, data=data))

    def action_xlsx_report_generate(self):
        """Here generate a dictionary of list of datas and that return to a
            report action. And it will generate the xlsx report. """
        data = {
            'stock_report': self.call_render_report(),
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'turnover.report',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Inventory Turnover Analysis Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """This function is for create xlsx report"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Inventory Turnover Analysis Report')
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '30px'})
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        sheet.merge_range('A3:G1', 'Inventory Turnover Analysis Report', head)
        row = 6
        column = 0
        if data['start_date']:
            sheet.write(5, 1, 'Start Date:', workbook.add_format({
                'align': 'center', 'bold': True}))
            sheet.write(5, 2, data['start_date'], workbook.add_format({
                'align': 'center', 'bold': True}))
            row += 1
        if data['end_date']:
            sheet.write(5, 4, 'End Date:', workbook.add_format({
                'align': 'center', 'bold': True}))
            sheet.write(5, 5, data['end_date'], workbook.add_format({
                'align': 'center', 'bold': True}))
            row += 1
        head_table = workbook.add_format({'align': 'center', 'bold': True})
        sheet.write(row, column, 'Product', workbook.add_format({
            'align': 'left', 'bold': True}))
        column += 1
        sheet.write(row, column, 'Opening Stock', head_table)
        column += 1
        sheet.write(row, column, 'Closing Stock', head_table)
        column += 1
        sheet.write(row, column, 'Average Stock', head_table)
        column += 1
        sheet.write(row, column, 'Sale count', head_table)
        column += 1
        sheet.write(row, column, 'Purchase Count', head_table)
        column += 1
        sheet.write(row, column, 'Turnover Ratio', head_table)
        for datas in data['stock_report']:
            row += 1
            column = 0
            table_body = workbook.add_format({'align': 'center'})
            sheet.write(row, column, datas['product'], workbook.add_format({
                'align': 'left'}))
            column += 1
            sheet.write(row, column, datas['opening_stock'], table_body)
            column += 1
            sheet.write(row, column, datas['closing_stock'], table_body)
            column += 1
            sheet.write(row, column, datas['average_stock'], table_body)
            column += 1
            sheet.write(row, column, datas['sale_count'], table_body)
            column += 1
            sheet.write(row, column, datas['purchase_count'], table_body)
            column += 1
            sheet.write(row, column, datas['turnover_ratio'], table_body)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def action_data_fetch(self):
        """Here generate a list of dictionary of datas, and from that list
        create records. And it will return tree view with created records."""
        self.env['fetch.data'].search([]).unlink()
        filtered_records = self.call_render_model()
        for rec in filtered_records:
            self.env['fetch.data'].create({
                'company_id': rec['company_id'],
                'warehouse_id': rec['warehouse_id'],
                'product_id': rec['id'],
                'category_id': rec['category_id'],
                'opening_stock': rec['opening_stock'],
                'closing_stock': rec['closing_stock'],
                'average_stock': rec['average_stock'],
                'sale_count': rec['sale_count'],
                'purchase_count': rec['purchase_count'],
                'turnover_ratio': rec['turnover_ratio'],
            })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'fetch.data',
            'name': 'Turnover Analysis Report',
            'target': 'current',
            'context': {"create": False},
        }

    def action_generate_graph_view(self):
        """Here generate a list of dictionary of datas, and from that list
        create records. And it will return graph view with created records."""
        self.env['turnover.graph.analysis'].search([]).unlink()
        filtered_records = self.call_render_model()
        for rec in filtered_records:
            self.env['turnover.graph.analysis'].create({
                'company_id': rec['company_id'],
                'warehouse_id': rec['warehouse_id'],
                'product_id': rec['id'],
                'category_id': rec['category_id'],
                'opening_stock': rec['opening_stock'],
                'closing_stock': rec['closing_stock'],
                'average_stock': rec['average_stock'],
                'sale_count': rec['sale_count'],
                'purchase_count': rec['purchase_count'],
                'turnover_ratio': rec['turnover_ratio'],
            })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'graph',
            'res_model': 'turnover.graph.analysis',
            'name': 'Turnover Analysis',
            'target': 'current',
            'context': {"create": False},
        }

    def call_render_report(self):
        """Function call for get datas to generate PDF and XLSX report, and
        return the computed record."""
        stock_report = []
        warehouse = False
        last_count_date = False
        domain = []
        domain_list = []
        domain.append(('product_id', 'in',
                       self.product_ids.ids), ) if self.product_ids else None
        domain.append(('company_id', 'in',
                       self.company_ids.ids), ) if self.company_ids else None
        domain.append(('product_categ_id', 'in',
                       self.category_ids.ids), ) if self.category_ids else None
        if self.warehouse_ids:
            for warehouse in self.warehouse_ids:
                domain_list += warehouse.lot_stock_id.search([
                    ('location_id', 'child_of',
                     warehouse.view_location_id.id)]).ids
            domain.append(('location_id', 'in', domain_list))
        quants = self.env['stock.quant'].search(domain)
        for quant in quants:
            closing_stock = 0
            opening_stock = 0
            sales_count = quant.product_id.sales_count
            purchase_count = quant.product_id.purchased_product_qty
            category_id = quant.product_id.categ_id.complete_name
            if quant.location_id.usage == 'internal':
                opening_stock += quant.available_quantity
                closing_stock += quant.quantity
                warehouse = quant.location_id.warehouse_id.name
                last_count_date = quant.last_count_date
            average_stock = (opening_stock + closing_stock) / 2
            stock_count = sales_count + opening_stock
            turnover_ratio = 0 if average_stock == 0 or stock_count == 0 else \
                stock_count / average_stock
            turnover = round(turnover_ratio, 2)
            name = quant.product_id.display_name
            split_name = name.split(']')
            product_name = split_name[0] if len(split_name) == 1 else \
                split_name[1]
            values = {'id': quant.product_id.id,
                      'product': product_name,
                      'last_count_date': last_count_date,
                      'opening_stock': opening_stock,
                      'closing_stock': closing_stock,
                      'average_stock': average_stock,
                      'sale_count': sales_count,
                      'purchase_count': purchase_count,
                      'turnover_ratio': turnover,
                      'category_id': category_id,
                      'company_id': quant.company_id.name,
                      'warehouse_id': warehouse}
            stock_report.append(values)
        return self._date_comparison(stock_report)

    def call_render_model(self):
        """Function call for get datas to generate list and graph view, and
        return the computed record."""
        stock_report = []
        warehouse = False
        last_count_date = False
        domain = []
        domain_list = []
        domain.append(('product_id', 'in',
                       self.product_ids.ids), ) if self.product_ids else None
        domain.append(('company_id', 'in',
                       self.company_ids.ids), ) if self.company_ids else None
        domain.append(('product_categ_id', 'in',
                       self.category_ids.ids), ) if self.category_ids else None
        if self.warehouse_ids:
            for warehouse in self.warehouse_ids:
                domain_list += warehouse.lot_stock_id.search(
                    [('location_id', 'child_of',
                      warehouse.view_location_id.id)]).ids
            domain.append(('location_id', 'in', domain_list))
        quants = self.env['stock.quant'].search(domain)
        for quant in quants:
            closing_stock = 0
            opening_stock = 0
            sales_count = quant.product_id.sales_count
            purchase_count = quant.product_id.purchased_product_qty
            category_id = quant.product_id.categ_id.id
            if quant.location_id.usage == 'internal':
                opening_stock += quant.available_quantity
                closing_stock += quant.quantity
                warehouse = quant.location_id.warehouse_id.id
                last_count_date = quant.last_count_date
            average_stock = (opening_stock + closing_stock) / 2
            stock_count = sales_count + opening_stock
            turnover_ratio = 0 if average_stock == 0 or stock_count == 0 else \
                stock_count / average_stock
            turnover = round(turnover_ratio, 2)
            values = {'id': quant.product_id.id,
                      'last_count_date': last_count_date,
                      'opening_stock': opening_stock,
                      'closing_stock': closing_stock,
                      'average_stock': average_stock,
                      'sale_count': sales_count,
                      'purchase_count': purchase_count,
                      'turnover_ratio': turnover,
                      'category_id': category_id,
                      'company_id': quant.company_id.id,
                      'warehouse_id': warehouse}
            stock_report.append(values)
        return self._date_comparison(stock_report)

    def _date_comparison(self, data):
        """Function is for filter data by selected date range."""
        filtered_records = []
        record_dict = {}
        for item in data:
            key = (item['id'], item['last_count_date'])
            if key in record_dict:
                record = record_dict[key]
                record['opening_stock'] += item['opening_stock']
                record['closing_stock'] += item['closing_stock']
            else:
                record_dict[key] = item
        for record in record_dict.values():
            record_date = record['last_count_date']
            if ((not self.start_date and not self.end_date) or
                    (self.start_date and self.end_date and
                     self.start_date <= self.end_date and
                     self.start_date <= record_date <= self.end_date) or
                    (self.start_date and not self.end_date and
                     record_date >= self.start_date) or
                    (not self.start_date and self.end_date and
                     record_date <= self.end_date)):
                if record['id'] in filtered_records:
                    filtered_record = filtered_records[record['id']]
                    filtered_record['opening_stock'] += record['opening_stock']
                    filtered_record['closing_stock'] += record['closing_stock']
                else:
                    filtered_records.append(record)
        return filtered_records
