# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api
import io
import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DynamicInventoryReport(models.Model):
    _name = "dynamic.inventory.report"

    purchase_report = fields.Char(string="Purchase Report")
    date_from = fields.Datetime(string="Date From")
    date_to = fields.Datetime(string="Date to")
    report_type = fields.Selection([
        ('report_by_transfers', 'Report By Transfers'),
        ('report_by_categories', 'Report By Categories'),
        ('report_by_warehouse', 'Report By Warehouse'),
        ('report_by_location', 'Report By Location')],
         default='report_by_transfers')

    @api.model
    def inventory_report(self, option):
        # orders = self.env['purchase.order'].search([])
        report_values = self.env['dynamic.inventory.report'].search(
            [('id', '=', option[0])])
        data = {
            'report_type': report_values.report_type,
            'model': self,
        }

        if report_values.date_from:
            data.update({
                'date_from': report_values.date_from,
            })
        if report_values.date_to:
            data.update({
                'date_to': report_values.date_to,
            })
        filters = self.get_filter(option)
        report = self._get_report_values(data)
        lines = self._get_report_values(data).get('INVENTORY')
        return {
            'name': "Inventory Orders",
            'type': 'ir.actions.client',
            'tag': 's_r',
            'orders': data,
            'filters': filters,
            'report_lines': lines,
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}
        if data.get('report_type') == 'report_by_transfers':
            filters['report_type'] = 'Report By Transfers'
        elif data.get('report_type') == 'report_by_categories':
            filters['report_type'] = 'Report By Categories'
        elif data.get('report_type') == 'report_by_warehouse':
            filters['report_type'] = 'Report By Warehouse'
        elif data.get('report_type') == 'report_by_location':
            filters['report_type'] = 'Report By Location'
        else:
            filters['report_type'] = 'report_by_transfers'

        return filters

    def get_filter_data(self, option):
        r = self.env['dynamic.inventory.report'].search([('id', '=', option[0])])
        default_filters = {}

        filter_dict = {
            'report_type': r.report_type,
        }
        filter_dict.update(default_filters)
        return filter_dict

    @api.model
    def create(self, vals):

        res = super(DynamicInventoryReport, self).create(vals)
        return res


    def write(self, vals):
        res = super(DynamicInventoryReport, self).write(vals)
        return res

    def _get_report_sub_lines(self, data, report, date_from, date_to):
        report_sub_lines = []
        new_filter = None

        if data.get('report_type') == 'report_by_transfers':
            query = '''
                             select l.name,l.partner_id,l.scheduled_date,l.origin,l.company_id,l.state,res_partner.name as partner,res_company.name as company,l.id as id
                             from stock_picking as l
                             left join res_partner on l.partner_id = res_partner.id
							 left join res_company on l.company_id = res_company.id
                              '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.scheduled_date >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.scheduled_date <= '%s' " % data.get('date_to')
            self._cr.execute(query)
            report_by_order = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order)
        elif data.get('report_type') == 'report_by_categories':
            query = '''
              select prop_date.res_id,prop_date.value_float,product_template.name,product_template.create_date,product_template.categ_id,product_product.id, stock_quant.quantity,product_category.name as category from product_product 
              inner join product_template on  product_product.product_tmpl_id = product_template.id 
			  inner join stock_quant on product_product.id = stock_quant.product_id
			  LEFT OUTER JOIN ir_property prop_date ON prop_date.res_id = CONCAT('product.product,', product_product.id) 
			  left join product_category on product_category.id = product_template.categ_id
                    '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.create_date >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.create_date <= '%s' " % data.get('date_to')
            self._cr.execute(query)
            report_by_order_details = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order_details)
        elif data.get('report_type') == 'report_by_warehouse':
            query = '''
            select l.name,l.company_id,l.view_location_id,l.reception_route_id as route,l.write_date,res_company.name as company,stock_location.name as location,stock_location_route.name as route
            from stock_warehouse as l
		    left join res_company on res_company.id = l.company_id
			left join stock_location on stock_location.id = l.view_location_id
			left join stock_location_route on stock_location_route.id = l.reception_route_id
		    '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.write_date >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.write_date <= '%s' " % data.get('date_to')
            self._cr.execute(query)
            report_by_product = self._cr.dictfetchall()
            report_sub_lines.append(report_by_product)
        elif data.get('report_type') == 'report_by_location':
            query = '''
            select l.complete_name,l.usage as location_type,l.create_date,l.company_id,res_company.name as company
            from stock_location as l
		    left join res_company on res_company.id = l.company_id
            '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.create_date >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.create_date <= '%s' " % data.get('date_to')
            self._cr.execute(query)
            report_by_categories = self._cr.dictfetchall()
            report_sub_lines.append(report_by_categories)
        return report_sub_lines

    def _get_report_total_value(self, data, report):
        report_main_lines = []
        if data.get('report_type') == 'report_by_order':
            self._cr.execute('''
                select count(so.id) as order,sum(so.amount_total) as amount
                from sale_order as so
                ''')
            report_by_order = self._cr.dictfetchall()
            report_main_lines.append(report_by_order)
        elif data.get('report_type') == 'report_by_order_detail':
            self._cr.execute('''
                            select count(so_line.id) as order,sum(so_line.price_subtotal) as total
                            from sale_order_line as so_line
                            ''')
            report_by_order_detail = self._cr.dictfetchall()
            report_main_lines.append(report_by_order_detail)
        elif data.get('report_type') == 'report_by_product':
            self._cr.execute('''
                select count(so_line.product_id) as order,sum(so_line.price_subtotal) as amount
                    from sale_order_line as so_line
                ''')
            report_by_product = self._cr.dictfetchall()
            report_main_lines.append(report_by_product)

        else:
            report_main_lines = False

        return report_main_lines

    def _get_report_values(self, data):
        docs = data['model']
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        if data['report_type'] == 'report_by_transfers':
            report = ['Report By Transfers']
        elif data['report_type'] == 'report_by_categories':
            report = ['Report By Categories']
        elif data['report_type'] == 'report_by_warehouse':
            report = ['Report By Warehouse']
        elif data['report_type'] == 'report_by_location':
            report = ['Report By Location']
        else:
            report = ['report_by_transfers By Order']

        if data.get('report_type'):
            report_res = \
                self._get_report_sub_lines(data, report, date_from, date_to)[0]
        else:
            report_res = self._get_report_sub_lines(data, report, date_from,
                                                    date_to)

        return {
            'doc_ids': self.ids,
            'docs': docs,
            'INVENTORY': report_res,

        }

    def get_inventory_xlsx_report(self, data, response, report_data, dfr_data):
        report_data_main = json.loads(report_data)
        output = io.BytesIO()
        filters = json.loads(data)

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 2,
             'border_color': 'black'})
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_l = workbook.add_format(
            {'font_size': '10px', 'border': 1, 'bold': True})
        txt_v = workbook.add_format(
            {'align': 'right', 'font_size': '10px', 'border': 1})
        sheet.merge_range('A2:H3',
                          'Purchase Report',
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        date_style = workbook.add_format({'align': 'center',
                                          'font_size': '10px'})

        if filters.get('report_type') == 'report_by_transfers':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Reference', heading)
            sheet.write('B7', 'Scheduled Date', heading)
            sheet.write('C7', 'Source Document', heading)
            sheet.write('D7', 'Company', heading)
            sheet.write('E7', 'Delivery Address', heading)
            sheet.write('F7', 'State', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)
            sheet.set_column(7, 4, 15)
            sheet.set_column(8, 5, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['scheduled_date'], txt_l)
                sheet.write(row, col + 2, rec_data['origin'], txt_l)
                sheet.write(row, col + 3, rec_data['company'], txt_l)
                sheet.write(row, col + 4, rec_data['partner'], txt_l)
                sheet.write(row, col + 5, rec_data['state'], txt_l)

        if filters.get('report_type') == 'report_by_categories':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Category', heading)
            sheet.write('B7', 'Product Name', heading)
            sheet.write('C7', 'Create Date', heading)
            sheet.write('D7', 'Product Cost', heading)
            sheet.write('E7', 'On Hand Qty', heading)
            # sheet.write('F7', 'Product Name', heading)
            # sheet.write('G7', 'Price unit', heading)
            # sheet.write('H7', 'Qty', heading)
            # sheet.write('I7', 'Price Total', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)
            sheet.set_column(7, 4, 15)
            sheet.set_column(8, 5, 15)
            sheet.set_column(9, 6, 15)
            sheet.set_column(10, 7, 15)
            sheet.set_column(11, 8, 15)
            sheet.set_column(12, 9, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['category'], txt_l)
                sheet.write(row, col + 1, rec_data['name'], txt_l)
                sheet.write(row, col + 2, rec_data['create_date'], txt_l)
                sheet.write(row, col + 3, rec_data['value_float'], txt_l)
                sheet.write(row, col + 4, rec_data['quantity'], txt_l)
                # sheet.write(row, col + 5, rec_data['product'], txt_l)
                # sheet.write(row, col + 6, rec_data['price_unit'], txt_l)
                # sheet.write(row, col + 7, rec_data['sum'], txt_l)
                # sheet.write(row, col + 8, rec_data['amount_total'], txt_l)

        if filters.get('report_type') == 'report_by_warehouse':
            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Warehouse', heading)
            sheet.write('B7', 'Date', heading)
            sheet.write('C7', 'Company', heading)
            sheet.write('D7', 'Location', heading)
            sheet.write('E7', 'Route', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)
            sheet.set_column(7, 4, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['write_date'], txt_l)
                sheet.write(row, col + 2, rec_data['company'], txt_l)
                sheet.write(row, col + 3, rec_data['location'], txt_l)
                sheet.write(row, col + 4, rec_data['route'], txt_l)

        if filters.get('report_type') == 'report_by_location':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('B7', 'Location', heading)
            sheet.write('C7', 'Location Type', heading)
            sheet.write('D7', 'Create Date', heading)
            sheet.write('E7', 'Company', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 1
            sheet.set_column(3, 1, 15)
            sheet.set_column(4, 2, 15)
            sheet.set_column(5, 3, 15)
            sheet.set_column(6, 4, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['complete_name'], txt_l)
                sheet.write(row, col + 1, rec_data['location_type'], txt_l)
                sheet.write(row, col + 2, rec_data['create_date'], txt_l)
                sheet.write(row, col + 3, rec_data['company'], txt_l)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
