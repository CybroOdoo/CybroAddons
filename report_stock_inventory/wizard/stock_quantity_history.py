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
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import date_utils, json_default

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class InventoryReport(models.TransientModel):
    """Transient model for generating inventory reports in Odoo."""
    _inherit = 'stock.quantity.history'

    location = fields.Many2many('stock.location', string='Location',
                                domain="[('usage', '=', 'internal')]",
                                help="Location Filter")
    category = fields.Many2many('product.category', string='Category',
                                help="Category Filter")

    def _get_category_ids(self):
        """ Helper method to fetch selected categories and their child categories recursively. """
        if not self.category:
            return []
        query = """
            WITH RECURSIVE CategoryHierarchy AS (
                SELECT id FROM product_category WHERE id IN %s
                UNION ALL 
                SELECT c.id FROM product_category c 
                JOIN CategoryHierarchy ch ON c.parent_id = ch.id
            ) SELECT DISTINCT id FROM CategoryHierarchy
        """
        self.env.cr.execute(query, (tuple(self.category.ids),))
        return [r[0] for r in self.env.cr.fetchall()]

    def _validate_data_exists(self):
        """ Helper method to check if matching quants exist before generating reports. """
        category_ids = self._get_category_ids()
        domain = [('is_storable', '=', True)]
        if category_ids:
            domain.append(('categ_id', 'in', category_ids))
        products = self.env['product.product'].search(domain)

        quant_found = False
        if products:
            quant_domain = [
                ('product_id', 'in', products.ids),
                ('location_id.usage', '=', 'internal'),
                ('company_id', '=', self.env.company.id)
            ]
            if self.location:
                quant_domain.append(('location_id', 'in', self.location.ids))
            if self.env['stock.quant'].search_count(quant_domain) > 0:
                quant_found = True

        if not quant_found:
            raise UserError(_("No data found for the selected criteria."))

    def open_at_date(self):
        """Action to open product list view for the inventory at date with wizard filters applied."""
        self._validate_data_exists()
        action = super().open_at_date()
        category_ids = self._get_category_ids()
        quant_domain = [
            ('location_id.usage', '=', 'internal'),
            ('company_id', '=', self.env.company.id),
            ('product_id.is_storable', '=', True),
        ]
        if category_ids:
            quant_domain.append(('product_id.categ_id', 'in', category_ids))
        if self.location:
            quant_domain.append(('location_id', 'in', self.location.ids))

        quants = self.env['stock.quant'].search(quant_domain)
        product_ids = quants.mapped('product_id').ids

        action['domain'] = expression.AND([action.get('domain', []), [('id', 'in', product_ids)]])
        ctx = dict(action.get('context', {}))
        if self.location:
            ctx['location'] = self.location.ids
        else:
            ctx['location'] = self.env['stock.location'].search([
                ('usage', '=', 'internal'),
                ('company_id', '=', self.env.company.id)
            ]).ids
        action['context'] = ctx
        return action

    def action_xlsx_report(self):
        """Action to generate XLSX report for stock inventory.
                :return: Dictionary with report data."""
        self._validate_data_exists()
        inventory_date = self.inventory_datetime.strftime('%Y-%m-%d')
        loc_name = ','.join(self.location.mapped('display_name'))
        categ_name = ','.join(self.category.mapped('name'))
        data = {
            'location': self.location.ids,
            'category': self.category.ids,
            'compute_at_date': self.open_at_date,
            'date': self.inventory_datetime,
            'loc_name': loc_name,
            'categ_name': categ_name,
            'inventory_date': inventory_date
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'stock.quantity.history',
                     'options': json.dumps(data,
                                           default=json_default),
                     'output_format': 'xlsx',
                     },
            'report_type': 'xlsx'
        }

    def action_print_pdf(self):
        """Action to print PDF report for stock inventory.
                :return: Report action."""
        self._validate_data_exists()
        inventory_date = self.inventory_datetime.strftime('%Y-%m-%d')
        loc_name = ','.join(self.location.mapped('display_name'))
        categ_name = ','.join(self.category.mapped('name'))
        data = {
            'location': self.location.ids,
            'category': self.category.ids,
            'compute_at_date': self.open_at_date,
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
        sheet.set_column('A:A', 5, cell_format)
        sheet.set_column('A:B', 20, cell_format)
        sheet.set_column('B:C', 25, cell_format)
        sheet.set_column('C:D', 9, cell_format)
        sheet.set_column('D:E', 13, cell_format)
        sheet.set_column('E:F', 8, cell_format)

        category_ids = data.get('category', [])
        if category_ids:
            query = """
                WITH RECURSIVE CategoryHierarchy AS (
                    SELECT id FROM product_category WHERE id IN %s
                    UNION ALL 
                    SELECT c.id FROM product_category c 
                    JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                ) SELECT DISTINCT id FROM CategoryHierarchy
            """
            self.env.cr.execute(query, (tuple(category_ids),))
            all_cat_ids = [r[0] for r in self.env.cr.fetchall()]
            product = self.env['product.product'].search(
                [('categ_id', 'in', all_cat_ids),
                 ('is_storable', '=', True)])
        else:
            product = self.env['product.product'].search(
                [('is_storable', '=', True)])
        if data.get('date'):
            sheet.write('A2', 'Date:', format6)
            sheet.write('B2', data.get('inventory_date', ''), format7)
        if data.get('loc_name') and not data.get('categ_name'):
            sheet.write('G2', 'Location(s):', format6)
            sheet.write('H2', data['loc_name'], format7)
        if data.get('categ_name') and not data.get('loc_name'):
            sheet.write('G2', 'Categories:', format6)
            sheet.write('H2', data['categ_name'], format7)
        if data.get('loc_name') and data.get('categ_name'):
            sheet.write('G2', 'Categories:', format6)
            sheet.write('H2', data['categ_name'], format7)
            sheet.write('G3', 'Locations:', format6)
            sheet.write('H3', data['loc_name'], format7)
        sheet.merge_range('B7:D7', 'Inventory Stock Reports', format2)
        sheet.write('A9', 'S NO', format4)
        sheet.write('B9', "Internal Reference", format4)
        sheet.write('C9', "Product", format4)
        sheet.write('D9', "Quantity", format4)
        sheet.write('E9', "Location", format4)
        sheet.write('F9', "Unit", format4)
        row_num = 9
        col_num = 0
        s_no = 1
        grouped_stock = {}
        for prod in product:
            rec = prod.with_context(
                {'location': data.get('location'), 'to_date': data.get('date')})
            if data.get('location'):
                stock = self.env['stock.quant'].search(
                    [('product_id', '=', rec.id),
                     ('location_id', 'in', data['location']),
                     ('location_id.usage', '=', 'internal'),
                     ('company_id', '=', self.env.company.id)])
            else:
                stock = self.env['stock.quant'].search(
                    [('product_id', '=', rec.id),
                     ('location_id.usage', '=', 'internal'),
                     ('company_id', '=', self.env.company.id)])
            for quant_id in stock:
                key = (quant_id.product_id.id, quant_id.location_id.id)
                if key not in grouped_stock:
                    grouped_stock[key] = {
                        'default_code': quant_id.product_id.default_code or '',
                        'product_name': quant_id.product_id.name or '',
                        'available_quantity': 0.0,
                        'location_name': quant_id.location_id.complete_name or '',
                        'uom_name': quant_id.product_uom_id.name or '',
                    }
                grouped_stock[key]['available_quantity'] += quant_id.available_quantity

        for item in grouped_stock.values():
            sheet.write(row_num, col_num, s_no, format9)
            sheet.write(row_num, col_num + 1, item['default_code'], format5)
            sheet.write(row_num, col_num + 2, item['product_name'], format5)
            sheet.write(row_num, col_num + 3, item['available_quantity'], format5)
            sheet.write(row_num, col_num + 4, item['location_name'], format5)
            sheet.write(row_num, col_num + 5, item['uom_name'], format5)
            row_num += 1
            s_no += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
