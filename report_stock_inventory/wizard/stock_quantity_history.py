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
import json
import io
from odoo import fields, models, _

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class InventoryReport(models.TransientModel):
    """Transient model for generating inventory reports in Odoo."""
    _inherit = 'stock.quantity.history'

    location = fields.Many2many(
        'stock.location', string='Location',
        domain="[('usage', '=', 'internal')]",
        help="Location Filter")
    category = fields.Many2many(
        'product.category',
        string='Category',
        help="Category Filter"
    )

    def action_xlsx_report(self):
        """Action to generate XLSX report for stock inventory.
                :return: Dictionary with report data."""
        inventory_date = self.inventory_datetime.strftime('%Y-%m-%d')
        loc_name = ''
        for loc in self.location:
            loc_name = loc_name + loc.display_name + ','
        loc_name = loc_name[:-1]
        categ_name = ''
        for categ in self.category:
            categ_name = categ_name + categ.name + ','
        categ_name = categ_name[:-1]
        data = {
            'location': self.location.ids,
            'category': self.category.ids,
            'compute_at_date': True,
            'date': self.inventory_datetime,
            'loc_name': loc_name,
            'categ_name': categ_name,
            'inventory_date': inventory_date
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'stock.quantity.history',
                     'options': json.dumps(data,
                                           default=str), # date_utils.json_default
                     'output_format': 'xlsx',
                     },
            'report_type': 'xlsx'
        }

    def action_print_pdf(self):
        """Action to print PDF report for stock inventory.
                :return: Report action."""
        inventory_date = self.inventory_datetime.strftime('%Y-%m-%d')
        loc_name = ''
        for loc in self.location:
            loc_name = loc_name + loc.display_name + ','
        loc_name = loc_name[:-1]
        categ_name = ''
        for categ in self.category:
            categ_name = categ_name + categ.name + ','
        categ_name = categ_name[:-1]
        data = {
            'location': self.location.ids,
            'category': self.category.ids,
            'compute_at_date': True,
            'date': self.inventory_datetime,
            'loc_name': loc_name,
            'categ_name': categ_name,
            'inventory_date': inventory_date
        }
        return self.env.ref(
            'report_stock_inventory.action_stock_pdf').report_action(self,
                                                                     data)

    def get_xlsx_report(self, data, response):
        """Generate XLSX report based on the provided data.
                :param data: Dictionary containing data for the report.
                :param response: HTTP response object."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()

        format1 = workbook.add_format(
            {'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3',
             'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format(
            {'font_size': 12, 'bold': True, 'border': 1,
             'bg_color': '#928E8E'})
        format4 = workbook.add_format(
            {'font_size': 10, 'bold': True, 'border': 1,
             'bg_color': '#D2D1D1'})
        sheet.set_column(6, 15,15)
        sheet.set_column(7, 15,15)
        format5 = workbook.add_format({'font_size': 10, 'border': 1})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10, 'bold': True})
        format9 = workbook.add_format({'font_size': 10, 'border': 1})
        format2.set_align('center', )
        format4.set_align('center')
        format6.set_align('right')
        format9.set_align('left')
        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'left'})
        sheet.set_column('A:A', 2, cell_format)
        sheet.set_column('A:B', 10, cell_format)
        sheet.set_column('B:C', 25, cell_format)
        sheet.set_column('C:D', 25, cell_format)
        sheet.set_column('D:E', 10, cell_format)
        sheet.set_column('E:F', 15, cell_format)
        # Build search domain for products
        product_domain = [('is_storable', '=', True)]
        if data['category']:
            product_domain.append(('categ_id', 'child_of', data['category']))
        products = self.env['product.product'].search(product_domain)

        # Build moves search domain up to the target date
        domain_moves = [
            ('product_id', 'in', products.ids),
            ('state', '=', 'done'),
            ('company_id', '=', self.env.company.id)
        ]
        if data['date']:
            domain_moves.append(('date', '<=', data['date']))

        if data['location']:
            domain_moves.append('|')
            domain_moves.append(('location_id', 'in', data['location']))
            domain_moves.append(('location_dest_id', 'in', data['location']))

        moves = self.env['stock.move'].search(domain_moves)

        # Find allowed internal locations
        loc_domain = [('usage', '=', 'internal'), ('company_id', 'in', [self.env.company.id, False])]
        if data['location']:
            loc_domain.append(('id', 'in', data['location']))
        internal_locs = self.env['stock.location'].search(loc_domain)
        internal_loc_ids = set(internal_locs.ids)

        # Compute stock balances per product and location
        balances = {}
        for move in moves:
            prod_id = move.product_id.id
            qty = move.product_qty
            src_id = move.location_id.id
            dest_id = move.location_dest_id.id

            if src_id in internal_loc_ids:
                key = (prod_id, src_id)
                balances[key] = balances.get(key, 0.0) - qty

            if dest_id in internal_loc_ids:
                key = (prod_id, dest_id)
                balances[key] = balances.get(key, 0.0) + qty

        # Prepare report rows
        report_rows = []
        for (prod_id, loc_id), qty in balances.items():
            if qty > 0.0:  # Only show non-zero positive inventory in locations
                prod = products.filtered(lambda p: p.id == prod_id)
                if not prod:
                    prod = self.env['product.product'].browse(prod_id)
                loc = internal_locs.filtered(lambda l: l.id == loc_id)
                if not loc:
                    loc = self.env['stock.location'].browse(loc_id)
                report_rows.append({
                    'product': prod,
                    'location_name': loc.complete_name or loc.name or '',
                    'qty_available': qty,
                    'uom_id': prod.uom_id.name or '',
                })

        if data['date']:
            sheet.write('A2', 'Date:', format6)
            sheet.write('B2', data['inventory_date'], format7)
        if data['loc_name'] and not data['categ_name']:
            sheet.write('G2', 'Location(s):', format6)
            sheet.write('H2', data['loc_name'], format7)
        if data['categ_name'] and not data['loc_name']:
            sheet.write('G2', 'Categories:', format6)
            sheet.write('H2', data['categ_name'], format7)
        if data['loc_name'] and data['categ_name']:
            sheet.write('G2', 'Categories:', format6)
            sheet.write('H2', data['categ_name'], format7)
            sheet.write('G3', 'Locations:', format6)
            sheet.write('H3', data['loc_name'], format7)
        sheet.merge_range('B7:D7', 'Inventory Stock Report', format2)
        sheet.write('A9', 'S NO', format4)
        sheet.write('B9', "Internal Reference", format4)
        sheet.write('C9', "Product", format4)
        sheet.write('D9', "Quantity", format4)
        sheet.write('E9', "Location", format4)
        sheet.write('F9', "Unit", format4)

        row_num = 9
        col_num = 0
        s_no = 1
        for row in report_rows:
            sheet.write(row_num, col_num, s_no, format9)
            sheet.write(row_num, col_num + 1, row['product'].default_code, format5)
            sheet.write(row_num, col_num + 2, row['product'].name, format5)
            sheet.write(row_num, col_num + 3, row['qty_available'], format5)
            sheet.write(row_num, col_num + 4, row['location_name'], format5)
            sheet.write(row_num, col_num + 5, row['uom_id'], format5)
            row_num += 1
            s_no += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
