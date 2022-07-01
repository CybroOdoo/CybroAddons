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


class SaleReportGenerator(models.Model):
    _name = "sales.report"

    sale_report = fields.Char(string="Sale Report")
    date_from = fields.Datetime(string="Date From")
    date_to = fields.Datetime(string="Date to")
    report_type = fields.Selection([
        ('report_by_order', 'Report By Order'),
        ('report_by_order_detail', 'Report By Order Detail'),
        ('report_by_product', 'Report By Product'),
        ('report_by_categories', 'Report By Categories'),
        ('report_by_salesperson', 'Report By Sales Person'),
        ('report_by_state', 'Report By State')], default='report_by_order')

    @api.model
    def sale_report(self, option):
        orders = self.env['sale.order'].search([])
        report_values = self.env['sales.report'].search(
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
        lines = self._get_report_values(data).get('SALE')
        main_line = self._get_report_values(data).get('sale_main')

        return {
            'name': "Sale Orders",
            'type': 'ir.actions.client',
            'tag': 's_r',
            'orders': data,
            'filters': filters,
            'report_lines': lines,
            'report_main_line': main_line,
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}
        if data.get('report_type') == 'report_by_order':
            filters['report_type'] = 'Report By Order'
        elif data.get('report_type') == 'report_by_order_detail':
            filters['report_type'] = 'Report By Order Detail'
        elif data.get('report_type') == 'report_by_product':
            filters['report_type'] = 'Report By Product'
        elif data.get('report_type') == 'report_by_categories':
            filters['report_type'] = 'Report By Categories'
        elif data.get('report_type') == 'report_by_salesperson':
            filters['report_type'] = 'Report By Sales Person'
        elif data.get('report_type') == 'report_by_state':
            filters['report_type'] = 'Report By State'
        else:
            filters['report_type'] = 'report_by_order'

        return filters

    def get_filter_data(self, option):
        r = self.env['sales.report'].search([('id', '=', option[0])])
        default_filters = {}

        filter_dict = {
            'report_type': r.report_type,
        }
        filter_dict.update(default_filters)
        return filter_dict

    @api.model
    def create(self, vals):

        res = super(SaleReportGenerator, self).create(vals)
        return res

    def write(self, vals):

        res = super(SaleReportGenerator, self).write(vals)
        return res

    def _get_report_sub_lines(self, data, report, date_from, date_to):
        report_sub_lines = []
        new_filter = None

        if data.get('report_type') == 'report_by_order':
            query = '''
                        select so.id,so.name as number,so.date_order,so.partner_id,so.amount_total,so.user_id,res_partner.name as customer,
                        res_users.partner_id as user_partner,so.id as id,sum(sale_order_line.product_uom_qty),
                        (SELECT res_partner.name as sales_man FROM res_partner WHERE res_partner.id = res_users.partner_id)
                        from sale_order as so
                        inner join res_partner on so.partner_id = res_partner.id
                        inner join res_users on so.user_id = res_users.id
                        inner join sale_order_line on so.id = sale_order_line.order_id
                        
                                 '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where so.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "so.date_order <= '%s' " % data.get('date_to')
            query += "group by so.user_id,res_users.partner_id," \
                     "res_partner.name,so.partner_id,so.date_order," \
                     "so.name,so.amount_total,so.id"
            self._cr.execute(query)
            report_by_order = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order)

        elif data.get('report_type') == 'report_by_order_detail':
            query = '''
                       SELECT  so.id,so.name as number,so.date_order,res_partner.name as customer,
                            rc.name as company,product_template.name as product,
                            product_product.default_code,so_line.product_uom_qty,
                            so_line.price_subtotal,so.amount_total,so.partner_id,
                            so.user_id,ru.id,so_line.product_id,sum(so_line.product_uom_qty),
                            (SELECT res_partner.name as salesman FROM res_partner
                            WHERE res_partner.id = res_users.partner_id) from sale_order as so
                            inner join sale_order_line as so_line on so.id = so_line.order_id
                            inner join product_product ON so_line.product_id=product_product.id
                            inner join product_template ON product_product.product_tmpl_id = product_template.id
                            inner join res_partner on so.partner_id=res_partner.id inner join res_users on so.user_id = res_users.id
                            inner join res_company as rc on so.company_id=rc.id
                            inner join res_users as ru on so.user_id=ru.id
                        '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where so.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "so.date_order <= '%s' " % data.get('date_to')
            query += ''' group by so.user_id, so.name, so.id,so.date_order,
                         res_partner.name,rc.name,product_template.name,
                         product_product.default_code,so_line.product_uom_qty,
                         so_line.price_subtotal,so.amount_total,so.partner_id,
                         so.user_id,ru.id,so_line.product_id,res_users.partner_id
                     '''
            self._cr.execute(query)
            report_by_order_details = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order_details)

        elif data.get('report_type') == 'report_by_product':
            query = '''
                        SELECT  so.id,so.date_order,product_template.name as product,
                            product_category.name as category,
                            product_product.default_code,so_line.product_uom_qty,
                            so.amount_total,so.name as number                              
                            From sale_order as so
                            inner join sale_order_line as so_line on so.id = so_line.order_id
                            inner join product_product ON so_line.product_id=product_product.id
                            inner join product_template ON product_product.product_tmpl_id = product_template.id
                            inner join product_category on product_category.id = product_template.categ_id
                    '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where so.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "so.date_order <= '%s' " % data.get('date_to')
            query += "group by so.id,so.date_order,product_template.name,product_category.name,product_product.default_code,so_line.product_uom_qty"
            self._cr.execute(query)
            report_by_product = self._cr.dictfetchall()
            report_sub_lines.append(report_by_product)

        elif data.get('report_type') == 'report_by_categories':
            query = '''
                        select product_category.name,sum(so_line.product_uom_qty) as qty,sum(so_line.price_subtotal) as amount_total
                            from sale_order_line as so_line
                            inner join product_template on so_line.product_id = product_template.id
                            inner join product_category on product_category.id = product_template.categ_id
                            inner join sale_order on so_line.order_id = sale_order.id
                    '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where sale_order.date_order >= '%s' " % data.get(
                    'date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "sale_order.date_order <= '%s' " % data.get(
                    'date_to')
            query += "group by product_category.name"
            self._cr.execute(query)
            report_by_categories = self._cr.dictfetchall()
            report_sub_lines.append(report_by_categories)

        elif data.get('report_type') == 'report_by_salesperson':
            query = '''
                        select res_partner.name,sum(sale_order_line.product_uom_qty) as qty,
                            sum(sale_order_line.price_subtotal) as amount,count(so.id) as order
                            from sale_order as so
                            inner join res_users on so.user_id = res_users.id
                            inner join res_partner on res_users.partner_id = res_partner.id
                            inner join sale_order_line on so.id = sale_order_line.order_id
                    '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where so.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "so.date_order <= '%s' " % data.get('date_to')
            query += "group by res_partner.name"
            self._cr.execute(query)
            report_by_salesperson = self._cr.dictfetchall()
            report_sub_lines.append(report_by_salesperson)

        elif data.get('report_type') == 'report_by_state':
            query = '''
                        select so.state,count(so.id),sum(sale_order_line.product_uom_qty) as qty,
                            sum(sale_order_line.price_subtotal) as amount from sale_order as so 
                            inner join sale_order_line on so.id = sale_order_line.order_id
                    '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where so.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "so.date_order <= '%s' " % data.get('date_to')
            query += "group by so.state"
            self._cr.execute(query)
            report_by_state = self._cr.dictfetchall()

            report_sub_lines.append(report_by_state)
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
        if data['report_type'] == 'report_by_order_detail':
            report = ['Report By Order Detail']
        elif data['report_type'] == 'report_by_product':
            report = ['Report By Product']
        elif data['report_type'] == 'report_by_categories':
            report = ['Report By Categories']
        elif data['report_type'] == 'report_by_salesperson':
            report = ['Report By Sales Person']
        elif data['report_type'] == 'report_by_state':
            report = ['Report By State']
        else:
            report = ['Report By Order']
        #
        report_res_total = self._get_report_total_value(data, report)
        if data.get('report_type'):
            report_res = \
                self._get_report_sub_lines(data, report, date_from, date_to)[0]
        else:
            report_res = self._get_report_sub_lines(data, report, date_from,
                                                    date_to)
        #
        if data.get('report_type') == 'report_by_order':
            report_res_total = self._get_report_total_value(data, report)[0]

        return {
            'doc_ids': self.ids,
            'docs': docs,
            'SALE': report_res,
            'sale_main': report_res_total,

        }

    def get_sale_xlsx_report(self, data, response, report_data, dfr_data):
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
                          'Sales Report',
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        date_style = workbook.add_format({'align': 'center',
                                          'font_size': '10px'})

        if filters.get('report_type') == 'report_by_order':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Sale', heading)
            sheet.write('B7', 'Date Order', heading)
            sheet.write('C7', 'Customer', heading)
            sheet.write('D7', 'Sales Person', heading)
            sheet.write('E7', 'Total Qty', heading)
            sheet.write('F7', 'Amount Total', heading)

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
                sheet.write(row, col, rec_data['number'], txt_l)
                sheet.write(row, col + 1, rec_data['date_order'], txt_l)
                sheet.write(row, col + 2, rec_data['customer'], txt_l)
                sheet.write(row, col + 3, rec_data['sales_man'], txt_l)
                sheet.write(row, col + 4, rec_data['sum'], txt_l)
                sheet.write(row, col + 5, rec_data['amount_total'], txt_l)

        if filters.get('report_type') == 'report_by_order_detail':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Sale', heading)
            sheet.write('B7', 'Date Order', heading)
            sheet.write('C7', 'Customer', heading)
            sheet.write('D7', 'Company', heading)
            sheet.write('E7', 'Sales Person', heading)
            sheet.write('F7', 'Product Name', heading)
            sheet.write('G7', 'Product Code', heading)
            sheet.write('H7', 'Quantity', heading)
            sheet.write('I7', 'Price Subtotal', heading)
            sheet.write('J7', 'Amount Total', heading)

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
                sheet.write(row, col, rec_data['number'], txt_l)
                sheet.write(row, col + 1, rec_data['date_order'], txt_l)
                sheet.write(row, col + 2, rec_data['customer'], txt_l)
                sheet.write(row, col + 3, rec_data['company'], txt_l)
                sheet.write(row, col + 4, rec_data['salesman'], txt_l)
                sheet.write(row, col + 5, rec_data['product'], txt_l)
                sheet.write(row, col + 6, rec_data['default_code'], txt_l)
                sheet.write(row, col + 7, rec_data['product_uom_qty'], txt_l)
                sheet.write(row, col + 8, rec_data['price_subtotal'], txt_l)
                sheet.write(row, col + 9, rec_data['amount_total'], txt_l)

        if filters.get('report_type') == 'report_by_product':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Product', heading)
            sheet.write('B7', 'Category', heading)
            sheet.write('C7', 'Product Code', heading)
            sheet.write('D7', 'Quantity', heading)
            sheet.write('E7', 'Amount Total', heading)

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
                sheet.write(row, col, rec_data['product'], txt_l)
                sheet.write(row, col + 1, rec_data['category'], txt_l)
                sheet.write(row, col + 2, rec_data['default_code'], txt_l)
                sheet.write(row, col + 3, rec_data['product_uom_qty'], txt_l)
                sheet.write(row, col + 4, rec_data['amount_total'], txt_l)

        if filters.get('report_type') == 'report_by_categories':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('B7', 'Category', heading)
            sheet.write('C7', 'Qty', heading)
            sheet.write('D7', 'Amount Total', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 1
            sheet.set_column(3, 1, 15)
            sheet.set_column(4, 2, 15)
            sheet.set_column(5, 3, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['qty'], txt_l)
                sheet.write(row, col + 2, rec_data['amount_total'], txt_l)

        if filters.get('report_type') == 'report_by_salesperson':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Sales Person', heading)
            sheet.write('B7', 'Total Order', heading)
            sheet.write('C7', 'Total Qty', heading)
            sheet.write('D7', 'Total Amount', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['order'], txt_l)
                sheet.write(row, col + 2, rec_data['qty'], txt_l)
                sheet.write(row, col + 3, rec_data['amount'], txt_l)

        if filters.get('report_type') == 'report_by_state':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'State', heading)
            sheet.write('B7', 'Total Count', heading)
            sheet.write('C7', 'Quantity', heading)
            sheet.write('D7', 'Amount', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                if rec_data['state'] == 'draft':
                    sheet.write(row, col, 'Quotation', txt_l)
                elif rec_data['state'] == 'sent':
                    sheet.write(row, col, 'Quotation Sent', txt_l)
                elif rec_data['state'] == 'sale':
                    sheet.write(row, col, 'Sale Order', txt_l)
                sheet.write(row, col + 1, rec_data['count'], txt_l)
                sheet.write(row, col + 2, rec_data['qty'], txt_l)
                sheet.write(row, col + 3, rec_data['amount'], txt_l)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
