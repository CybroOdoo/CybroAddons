# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or
#    sell copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
import json
import io
from odoo import fields, models
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class IrActionsXlsxDownload(models.Model):
    _name = 'ir_actions_xlsx_download'
    _description = 'Action XLSX Download'
    _inherit = 'ir.actions.actions'
    _table = 'ir_actions'
    type = fields.Char(default='ir_actions_xlsx_download')


class RouteReport(models.TransientModel):
    """Transient model for the wizard"""
    _name = 'route.report'
    _description = 'Route Report'

    route = fields.Many2many('delivery.route', string='Route')
    payment = fields.Boolean(string='Show Due Amount')
    consolidated = fields.Boolean(string='Total Due only')

    def print_route_details(self):
        """Action on button to print pdf report"""
        data = {
            'route': self.route.read(['name']),
            'route_lines': self.route.route_lines.read(),
            'payment': self.payment,
            'consolidated': self.consolidated,
        }
        return self.env.ref(
            'customer_route_management.report_route_report').report_action(self,
                                                                           data=data)

    def print_xlsx_report_route(self):
        """Action on button to print xlsx report"""
        data = {
            'model': self._name,
            'route': self.route.ids,
            'payment': self.payment,
            'consolidated': self.consolidated
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'route.report',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Customer Route Management Report',
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, data, response):
        """Get xlsx report"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        cell_format = workbook.add_format(
            {'align': 'center', 'bold': True, 'bg_color': '#d3d3d3;',
             'color': '#191081'})
        left = workbook.add_format({'align': 'left'})
        loc_bold = workbook.add_format({'bold': True})
        color = workbook.add_format({'color': '#031311;'})
        if data['payment']:
            bold = workbook.add_format({'bold': True, 'align': 'left'})
        else:
            bold = workbook.add_format({'align': 'left'})
        docs = self.env['delivery.route'].search(
                [('id', 'in', data['route'])])
        for o in docs:
            sheet = workbook.add_worksheet(o.name)
            i = 3
            sheet.merge_range('F1:J1', o.name.upper(), cell_format)
            for l in o.route_lines:
                if (l.route):
                    sheet.merge_range(
                        'A' + str(i - 1) + ':' + 'B' + str(i - 1),
                        l.route.upper() + ':', loc_bold)
                if data['payment'] and not data['consolidated']:
                    sheet.merge_range(
                        'D' + str(i - 1) + ':' + 'E' + str(i - 1),
                        'Invoice Number', bold)
                    sheet.merge_range(
                        'F' + str(i - 1) + ':' + 'G' + str(i - 1), 'Date',
                        bold)
                    sheet.merge_range(
                        'H' + str(i - 1) + ':' + 'I' + str(i - 1),
                        'Amount Due', bold)
                for v in l.cust_tree:
                    address = str(v.street) + " " + str(v.street2) + \
                              " " + str(v.city) + " " + str(
                        v.state_id.name) + " " + str(v.zip) + \
                              " " + str(v.country_id.name) + " " + str(
                        v.email)
                    if data['payment'] and not data['consolidated']:
                        sheet.merge_range(
                            'B' + str(i) + ':' + 'C' + str(i),
                            str(v.name) + " " + str(v.phone) + " " +
                            address.replace('False', ''), color)
                    else:
                        sheet.merge_range(
                            'B' + str(i) + ':' + 'C' + str(i),
                            str(v.name).replace('False', ''), color)
                        sheet.merge_range(
                            'D' + str(i) + ':' + 'E' + str(i),
                            str(v.phone).replace('False', ''), color)
                        sheet.merge_range(
                            'F' + str(i) + ':' + 'G' + str(i),
                            address.replace('False', ''), color)
                    i += 1
                    if data['payment']:
                        total = 0.0
                        for dues in v.get_all_dues():
                            total += dues['amount_residual_signed']
                            if not data['consolidated']:
                                sheet.merge_range(
                                    'D' + str(i) + ':' + 'E' + str(i),
                                    dues['name'], left)
                                sheet.merge_range(
                                    'F' + str(i) + ':' + 'G' + str(i),
                                    str(dues['invoice_date_due'].strftime(
                                        "%B-%d-%Y")), left)
                                if self.env.user.company_id.currency_id.position == 'after':
                                    sheet.merge_range(
                                        'H' + str(i) + ':' + 'I' + str(i),
                                        str("{:.2f}".format(dues[
                                                                'amount_residual_signed']))
                                        + str(
                                            self.env.user.company_id.currency_id.symbol),
                                        left)
                                else:
                                    sheet.merge_range(
                                        'H' + str(i) + ':' + 'I' + str(i),
                                        str(self.env.user.company_id.currency_id.symbol) +
                                        str("{:.2f}".format(dues[
                                                                'amount_residual_signed']))
                                        , bold)
                                i += 1
                        if total != 0.0:
                            sheet.merge_range(
                                'D' + str(i) + ':' + 'E' + str(i), 'Total',
                                bold)
                            sheet.merge_range(
                                'F' + str(i) + ':' + 'G' + str(i), '',
                                left)
                            if self.env.user.company_id.currency_id.position == 'after':
                                sheet.merge_range(
                                    'H' + str(i) + ':' + 'I' + str(i),
                                    str("{:.2f}".format(total)) +
                                    str(self.env.user.company_id.currency_id.symbol),
                                    bold)
                            else:
                                sheet.merge_range(
                                    'H' + str(i) + ':' + 'I' + str(i),
                                    str(self.env.user.company_id.currency_id.symbol) +
                                    str("{:.2f}".format(total))
                                    , bold)
                            i += 1
                i += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
