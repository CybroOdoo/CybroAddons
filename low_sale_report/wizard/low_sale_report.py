# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import io
import json
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
from dateutil.relativedelta import relativedelta
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class LowSaleReport(models.TransientModel):
    """Its define as the sale low performance product details in pivot view and
     the Excel report."""
    _name = 'low.sale.report'
    _description = 'Low Sale Report'

    product_type = fields.Selection(
        [('variant', 'By product variant'),
         ('template', 'By product templates')], string="Report Type",
        help='Which sale to take into account: Product templates in general'
             ' or variants?', required=True)
    analysed_period_start = fields.Date(string='Period under analysis',
                                        help='If not chosen, all product sale'
                                             ' will be analysed')
    analysed_period_end = fields.Date(string='Period under analysis',
                                      help='If not chosen, all product sale'
                                           ' will be analysed',
                                      default=fields.Date.today())
    absolute_qty = fields.Float(string='Critical Level(Absolute Quantity)',
                                help='Which sale level are considered to be'
                                     ' low(in default unit of measurement) ',
                                required=True)
    category = fields.Many2one('product.category',
                               string='Product Categories',
                               help='If not chosen, all product categories '
                                    'wil be analysed')
    sale_team = fields.Many2one('crm.team',
                                help='If not chosen, all the sale team will'
                                     ' be analysed', string='Sales Teams')

    def action_pivot_low_sale_report(self):
        """Exporting the low sale report as the pivot view format in odoo"""
        low_sale_report = {
            'product_type': self.product_type,
            'analysed_period_start': self.analysed_period_start,
            'analysed_period_end': self.analysed_period_end,
            'absolute_qty': self.absolute_qty,
            'category': self.category,
            'sale_team': self.sale_team
        }
        pivot_data = self.env['low.sale.pivot.view.report'].get_data(
            low_sale_report)
        if not pivot_data:
            raise ValidationError(
                _("No data was found for the specified criteria"))
        pivot_records = []
        for data in pivot_data:
            values = {
                'price_total': data[2],
                'product_uom_qty': data[1]
            }
            if self.product_type == 'variant':
                values['product_id'] = data[0]
                view_id = self.env.ref(
                    'low_sale_report.'
                    'low_sale_pivot_view_report_view_pivot_variant').id
            else:
                values['product_tmpl_id'] = data[0]
                view_id = self.env.ref(
                    'low_sale_report.'
                    'low_sale_pivot_view_report_view_pivot_template').id
            pivot_data_records = self.env['low.sale.pivot.view.report'].create(
                values)
            pivot_records.append(pivot_data_records.id)
        return {
            'name': 'Low Sale Pivot View Report',
            'type': 'ir.actions.act_window',
            'res_model': 'low.sale.pivot.view.report',
            'view_mode': 'pivot',
            'view_id': view_id,
            'domain': [('id', 'in', pivot_records)],
        }

    def action_excel_low_sale_report(self):
        """Exporting the low sale report as the Excel view format in odoo"""
        self.ensure_one()
        data = {'ids': self.env.context.get('active_ids', []),
                'model': self.env.context.get('active_model', 'ir.ui.menu'),
                'form': self.read(
                    ['product_type', 'analysed_period_start',
                     'analysed_period_end', 'absolute_qty',
                     'category', 'sale_team'])[0]}
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'low.sale.report',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Low Sale Report',
                     },
            'report_type': 'low_sale_xlsx_download'
        }

    def get_low_sale_xlsx_report(self, options, response):
        """Generate the Excel report based on the provided options and write it
         to the response."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data = {'form': options['form'], 'model': 'ir.ui.menu', 'ids': []}
        data['form']['used_context'] = {
            'product_type': options['form']['product_type'],
            'analysed_period_start': options['form']['analysed_period_start'],
            'analysed_period_end': options['form']['analysed_period_end'],
            'absolute_qty': options['form']['absolute_qty'],
            'active_model': None,
            'active_ids': None,
            'active_id': None,
            'category': options['form']['category'],
            'sale_team': options['form']['sale_team'],
        }
        form_data = data['form']
        fetch_datas = self.env['low.sale.pivot.view.report'].get_data(form_data)
        if not fetch_datas:
            raise ValidationError(
                _("No data was found for the specified criteria."))
        worksheet = workbook.add_worksheet()
        name_formate = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'bg_color': '#D3D3D3', 'font_size': 16})
        format2 = workbook.add_format(
            {'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        rows = 0
        cols = 0
        worksheet.merge_range(rows, cols, rows + 1, cols + 3,
                              'Low Sale Report', name_formate)
        worksheet.set_column('B:B', 35)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.write('A4', "ID", format2)
        worksheet.write('B4', "Product", format2)
        worksheet.write('C4', "Sold Quantity", format2)
        worksheet.write('D4', "Revenue", format2)
        # Write data to the worksheet
        row_num = 5
        cols_num = 0
        for rec in fetch_datas:
            worksheet.write(row_num, cols_num, rec[0])
            worksheet.write(row_num, cols_num + 1, rec[3])
            worksheet.write(row_num, cols_num + 2, rec[1])
            worksheet.write(row_num, cols_num + 3, rec[2])
            row_num += 1
        # Close the workbook
        workbook.close()
        # Seek to the beginning of the BytesIO buffer
        output.seek(0)
        # Stream the Excel file to the response
        response.stream.write(output.read())
        output.close()

    @api.model
    def default_get(self, fields):
        """Prefilling the wizard data into the settings field values"""
        res = super().default_get(fields)
        # Fetch configuration parameters from ResConfigSettings
        config_params = self.env['ir.config_parameter'].sudo()
        # Prefill the values based on the configuration parameters
        res['product_type'] = config_params.get_param(
            'low_sale_report.product_type', default='variant')
        res['absolute_qty'] = config_params.get_param(
            'low_sale_report.absolute_qty', default=0.0)
        end_date = res.get('analysed_period_end')
        if end_date:
            if (config_params.get_param('low_sale_report.analysed_period') ==
                    'last_month'):
                start_date = end_date - relativedelta(days=30)
            elif (config_params.get_param('low_sale_report.analysed_period') ==
                  'last_3'):
                start_date = end_date - relativedelta(months=3)
            elif (config_params.get_param('low_sale_report.analysed_period') ==
                  'last_6'):
                start_date = end_date - relativedelta(months=6)
            elif (config_params.get_param('low_sale_report.analysed_period') ==
                  'last_12'):
                start_date = end_date - relativedelta(months=12)
            else:
                # Default to last_month if no valid option is selected
                start_date = end_date - relativedelta(months=12)
            res['analysed_period_start'] = start_date
        return res
