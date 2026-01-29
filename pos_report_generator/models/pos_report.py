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


class PosReportGenerator(models.Model):
    _name = "pos.report"

    pos_report = fields.Char(string="PoS Report")
    date_from = fields.Datetime(string="Date From")
    date_to = fields.Datetime(string="Date to")
    report_type = fields.Selection([('report_by_order', 'Report By Order'),
                                    ('report_by_order_detail', 'Report By Order Detail'),
                                    ('report_by_product', 'Report By Product'),
                                    ('report_by_categories', 'Report By Categories'),
                                    ('report_by_salesman', 'Report By Salesman'),
                                    ('report_by_payment', 'Report By Payment')],
                                   default='report_by_order')

    @api.model
    def pos_report(self, option):
        orders = self.env['pos.order'].search([])
        report_values = self.env['pos.report'].search([('id', '=', option[0])])
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
        # print("reports",reports)
        filters = self.get_filter(option)
        report = self._get_report_values(data)
        lines = self._get_report_values(data).get('POS')
        main_line = self._get_report_values(data).get('pos_main')

        return {
            'name': "PoS Orders",
            'type': 'ir.actions.client',
            'tag': 'pos_r',
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
        elif data.get('report_type') == 'report_by_salesman':
            filters['report_type'] = 'Report By Salesman'
        elif data.get('report_type') == 'report_by_payment':
            filters['report_type'] = 'Report By Payment'
        else:
            filters['report_type'] = 'report_by_order'

        return filters

    def get_filter_data(self, option):
        r = self.env['pos.report'].search([('id', '=', option[0])])
        default_filters = {}


        filter_dict = {
            'report_type': r.report_type,
        }
        filter_dict.update(default_filters)
        return filter_dict

    @api.model
    def create(self, vals):
        print("vals", vals)

        res = super(PosReportGenerator, self).create(vals)
        return res

    def write(self, vals):


        res = super(PosReportGenerator, self).write(vals)
        return res

    def _get_report_sub_lines(self, data, report, date_from, date_to):
        report_sub_lines = []
        new_filter = None

        if data.get('report_type') == 'report_by_order':
            query = '''
                    select l.name,l.date_order,l.partner_id,l.amount_total,l.note,l.user_id,res_partner.name,l.name as shop,pos_session.name as session,
                    res_users.partner_id as user_partner,sum(pos_order_line.qty),l.id as id,
                    (SELECT res_partner.name as salesman FROM res_partner WHERE res_partner.id = res_users.partner_id)
                    from pos_order as l 
                    left join pos_session on l.session_id = pos_session.id 
                    left join res_partner on l.partner_id = res_partner.id
                    left join res_users on l.user_id = res_users.id
                    left join pos_order_line on l.id = pos_order_line.order_id
                             '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by l.user_id,res_users.partner_id,res_partner.name,l.partner_id,l.date_order,pos_session.name,l.session_id,l.name,l.amount_total,l.note,l.id"
            self._cr.execute(query)
            report_by_order = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order)
        elif data.get('report_type') == 'report_by_order_detail':
            query = '''
            
            select l.name,l.date_order,l.partner_id,l.amount_total,l.note,l.user_id,res_partner.name,l.name as shop,pos_session.name as session,
             res_users.partner_id as user_partner,sum(pos_order_line.qty), pos_order_line.full_product_name, pos_order_line.price_unit,pos_order_line.price_subtotal,pos_order_line.price_subtotal_incl,pos_order_line.product_id,product_product.default_code,
             (SELECT res_partner.name as salesman FROM res_partner WHERE res_partner.id = res_users.partner_id)
             from pos_order as l 
             left join pos_session on l.session_id = pos_session.id 
             left join res_partner on l.partner_id = res_partner.id
             left join res_users on l.user_id = res_users.id
             left join pos_order_line on l.id = pos_order_line.order_id
            left join product_product on pos_order_line.product_id = product_product.id
                    '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by l.user_id,res_users.partner_id,res_partner.name,l.partner_id,l.date_order,pos_session.name,l.session_id,l.name,l.amount_total,l.note,pos_order_line.full_product_name,pos_order_line.price_unit,pos_order_line.price_subtotal,pos_order_line.price_subtotal_incl,pos_order_line.product_id,product_product.default_code"
            self._cr.execute(query)
            report_by_order_details = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order_details)
        elif data.get('report_type') == 'report_by_product':
            query ='''
            select l.amount_total,l.amount_paid,sum(pos_order_line.qty) as qty, pos_order_line.full_product_name, pos_order_line.price_unit,product_product.default_code,product_category.name
            from pos_order as l 
            left join pos_order_line on l.id = pos_order_line.order_id
            left join product_product on pos_order_line.product_id = product_product.id
            left join product_template on pos_order_line.product_id = product_template.id
            left join product_category on product_category.id = product_template.categ_id
                               '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by l.amount_total,l.amount_paid,pos_order_line.full_product_name,pos_order_line.price_unit,pos_order_line.product_id,product_product.default_code,product_template.categ_id,product_category.name"
            self._cr.execute(query)
            report_by_product = self._cr.dictfetchall()
            report_sub_lines.append(report_by_product)
        elif data.get('report_type') == 'report_by_categories':
            query ='''
            select product_category.name,sum(l.qty) as qty,sum(l.price_subtotal) as amount_total,sum(price_subtotal_incl) as total_incl
            from pos_order_line as l
            left join product_template on l.product_id = product_template.id
            left join product_category on product_category.id = product_template.categ_id
            left join pos_order on l.order_id = pos_order.id
            '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where pos_order.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "pos_order.date_order <= '%s' " % data.get('date_to')
            query += "group by product_category.name"
            self._cr.execute(query)
            report_by_categories = self._cr.dictfetchall()
            report_sub_lines.append(report_by_categories)
        elif data.get('report_type') == 'report_by_salesman':
           query ='''
           select res_partner.name,sum(pos_order_line.qty) as qty,sum(pos_order_line.price_subtotal) as amount,count(l.id) as order
           from pos_order as l
           left join res_users on l.user_id = res_users.id
           left join res_partner on res_users.partner_id = res_partner.id
           left join pos_order_line on l.id = pos_order_line.order_id
           '''
           term = 'Where '
           if data.get('date_from'):
               query += "Where l.date_order >= '%s' " % data.get('date_from')
               term = 'AND '
           if data.get('date_to'):
               query += term + "l.date_order <= '%s' " % data.get('date_to')
           query += "group by res_partner.name"
           self._cr.execute(query)
           report_by_salesman = self._cr.dictfetchall()
           report_sub_lines.append(report_by_salesman)
        elif data.get('report_type') == 'report_by_payment':
            query ='''
           select pos_payment_method.name,sum(l.amount_total),pos_session.name as session,pos_config.name as config
           from pos_order as l 
           left join pos_payment on l.id = pos_payment.pos_order_id
           left join pos_payment_method on pos_payment.payment_method_id = pos_payment_method.id
           left join pos_session on l.session_id = pos_session.id
           left join pos_config on pos_session.config_id = pos_config.id
            '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by pos_payment_method.name,pos_session.name,pos_config.name"
            self._cr.execute(query)
            report_by_payment = self._cr.dictfetchall()

            report_sub_lines.append(report_by_payment)
        return report_sub_lines

    def _get_report_total_value(self, data, report):
        report_main_lines = []
        if data.get('report_type') == 'report_by_order':
            self._cr.execute('''
            select count(l.id) as order,sum(l.amount_total) as amount
            from pos_order as l
            ''')
            report_by_order = self._cr.dictfetchall()
            report_main_lines.append(report_by_order)
        elif data.get('report_type') == 'report_by_order_detail':
            self._cr.execute('''
                        select count(line.id) as order,sum(line.price_subtotal) as total,sum(line.price_subtotal_incl)
                        from pos_order_line as line
                        ''')
            report_by_order_detail = self._cr.dictfetchall()
            report_main_lines.append(report_by_order_detail)
        elif data.get('report_type') == 'report_by_product':
            self._cr.execute('''
            select count(l.product_id) as order,sum(l.price_subtotal) as amount
                from pos_order_line as l
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
        elif data['report_type'] == 'report_by_salesman':
            report = ['Report By Salesman']
        elif data['report_type'] == 'report_by_payment':
            report = ['Report By Payment']
        else:
            report = ['Report By Order']

        report_res_total = self._get_report_total_value(data, report)
        if data.get('report_type'):
            report_res = self._get_report_sub_lines(data, report, date_from, date_to)[0]
        else:
            report_res = self._get_report_sub_lines(data, report, date_from, date_to)

        if data.get('report_type') == 'report_by_order':
            report_res_total = self._get_report_total_value(data, report)[0]

        return {
            'doc_ids': self.ids,
            'docs': docs,
            'POS': report_res,
            'pos_main': report_res_total,

        }

    def get_pos_xlsx_report(self, data, response, report_data, dfr_data):
        print("fhccccccgjk")
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
                          'Point of Sale Report',
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        date_style = workbook.add_format({'align': 'center',
                                          'font_size': '10px'})

        if filters.get('report_type') == 'report_by_order':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'PoS', heading)
            sheet.write('B7', 'Order', heading)
            sheet.write('C7', 'Date Order', heading)
            sheet.write('D7', 'Customer', heading)
            sheet.write('E7', 'Salesman', heading)
            sheet.write('F7', 'Total Qty', heading)
            sheet.write('G7', 'Amount Total', heading)
            sheet.write('H7', 'Note', heading)

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

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                print("iiii", rec_data)
                row += 1
                sheet.write(row, col, rec_data['shop'], txt_l)
                sheet.write(row, col + 1, rec_data['session'], txt_l)
                sheet.write(row, col + 2, rec_data['date_order'], txt_l)
                sheet.write(row, col + 3, rec_data['name'], txt_l)
                sheet.write(row, col + 4, rec_data['salesman'], txt_l)
                sheet.write(row, col + 5, rec_data['sum'], txt_l)
                sheet.write(row, col + 6, rec_data['amount_total'], txt_l)
                sheet.write(row, col + 7, rec_data['note'], txt_l)

        if filters.get('report_type') == 'report_by_order_detail':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'PoS', heading)
            sheet.write('B7', 'Order', heading)
            sheet.write('C7', 'Date Order', heading)
            sheet.write('D7', 'Customer', heading)
            sheet.write('E7', 'Salesman', heading)
            sheet.write('F7', 'Product Code', heading)
            sheet.write('G7', 'Product Name', heading)
            sheet.write('H7', 'Price unit', heading)
            sheet.write('I7', 'Qty', heading)
            sheet.write('J7', 'Price Subtotal', heading)
            sheet.write('K7', 'Price Subtotal Incl', heading)

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
                print("iiii", rec_data)
                row += 1
                sheet.write(row, col, rec_data['shop'], txt_l)
                sheet.write(row, col + 1, rec_data['session'], txt_l)
                sheet.write(row, col + 2, rec_data['date_order'], txt_l)
                sheet.write(row, col + 3, rec_data['name'], txt_l)
                sheet.write(row, col + 4, rec_data['salesman'], txt_l)
                sheet.write(row, col + 5, rec_data['default_code'], txt_l)
                sheet.write(row, col + 6, rec_data['full_product_name'], txt_l)
                sheet.write(row, col + 7, rec_data['price_unit'], txt_l)
                sheet.write(row, col + 8, rec_data['sum'], txt_l)
                sheet.write(row, col + 9, rec_data['price_subtotal'], txt_l)
                sheet.write(row, col + 10, rec_data['price_subtotal_incl'], txt_l)

        if filters.get('report_type') == 'report_by_product':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Category', heading)
            sheet.write('B7', 'Product Code', heading)
            sheet.write('C7', 'Product Name', heading)
            sheet.write('D7', 'Qty', heading)
            sheet.write('E7', 'Amount Total', heading)
            sheet.write('F7', 'Amount Total Incl', heading)

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
            # sheet.set_column(9, 6, 15)
            # sheet.set_column(10, 7, 15)
            # sheet.set_column(11, 8, 15)
            # sheet.set_column(12, 9, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                print("iiii", rec_data)
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['default_code'], txt_l)
                sheet.write(row, col + 2, rec_data['full_product_name'], txt_l)
                sheet.write(row, col + 3, rec_data['qty'], txt_l)
                sheet.write(row, col + 4, rec_data['amount_total'], txt_l)
                sheet.write(row, col + 5, rec_data['amount_paid'], txt_l)

        if filters.get('report_type') == 'report_by_categories':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Category', heading)
            sheet.write('B7', 'Qty', heading)
            sheet.write('C7', 'Amount Total', heading)
            sheet.write('D7', 'Amount Total Incl', heading)

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
                print("iiii", rec_data)
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['qty'], txt_l)
                sheet.write(row, col + 2, rec_data['amount_total'], txt_l)
                sheet.write(row, col + 3, rec_data['total_incl'], txt_l)

        if filters.get('report_type') == 'report_by_salesman':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Salesman', heading)
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
                print("iiii", rec_data)
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['order'], txt_l)
                sheet.write(row, col + 2, rec_data['qty'], txt_l)
                sheet.write(row, col + 3, rec_data['amount'], txt_l)

        if filters.get('report_type') == 'report_by_payment':

            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Point of Sale', heading)
            sheet.write('B7', 'PoS Session', heading)
            sheet.write('C7', 'Payment', heading)
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
                print("iiii", rec_data)
                row += 1
                sheet.write(row, col, rec_data['config'], txt_l)
                sheet.write(row, col + 1, rec_data['session'], txt_l)
                sheet.write(row, col + 2, rec_data['name'], txt_l)
                sheet.write(row, col + 3, rec_data['sum'], txt_l)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
