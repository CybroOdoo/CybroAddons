# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.info)
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
##############################################################################
import io
import json
import re
from datetime import datetime

from odoo import api, fields, models

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DynamicPurchaseReport(models.Model):
    """ Model for getting dynamic purchase report """
    _name = "dynamic.purchase.report"
    _description = "Dynamic Purchase Report"

    purchase_report = fields.Char(string="Purchase Report",
                                  help='Name of the report')
    date_from = fields.Datetime(string="Date From", help='Start date of report')
    date_to = fields.Datetime(string="Date to", help='End date of report')
    report_type = fields.Selection([
        ('report_by_order', 'Report By Order'),
        ('report_by_order_detail', 'Report By Order Detail'),
        ('report_by_product', 'Report By Product'),
        ('report_by_categories', 'Report By Categories'),
        ('report_by_purchase_representative',
         'Report By Purchase Representative'),
        ('report_by_state', 'Report By State')], default='report_by_order',
        help='The order of the report')

    @api.model
    def purchase_report(self, option):
        """ Function for getting datas for requests """
        report_values = self.env['dynamic.purchase.report'].browse(option[0])
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
        lines = self._get_report_values(data).get('PURCHASE')

        return {
            'name': "Purchase Orders",
            'type': 'ir.actions.client',
            'tag': 's_r',
            'orders': data,
            'filters': filters,
            'report_lines': lines,
        }

    def get_filter(self, option):
        """Function for get data according to order_by filter"""
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
        elif data.get('report_type') == 'report_by_purchase_representative':
            filters['report_type'] = 'Report By Purchase Representative'
        elif data.get('report_type') == 'report_by_state':
            filters['report_type'] = 'Report By State'
        else:
            filters['report_type'] = 'report_by_order'
        return filters

    def get_filter_data(self, option):
        """Function for get filter data in report"""
        record = self.env['dynamic.purchase.report'].browse(option[0])
        default_filters = {}
        filter_dict = {
            'report_type': record.report_type,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_report_sub_lines(self, data):
        """Function for get report value using sql query"""
        report_sub_lines = []
        if data.get('report_type') == 'report_by_order':
            query = """ select l.name,l.date_order, l.partner_id,l.amount_total,
            l.notes,l.user_id,res_partner.name as partner,
            res_users.partner_id as user_partner,sum(purchase_order_line.product_qty),
            l.id as id,(SELECT res_partner.name as salesman FROM res_partner
            WHERE res_partner.id = res_users.partner_id) from purchase_order as l
            left join res_partner on l.partner_id = res_partner.id
            left join res_users on l.user_id = res_users.id
            left join purchase_order_line on l.id = purchase_order_line.order_id 
            where 1=1 """
            if data.get('date_from'):
                query += """and l.date_order >= '%s' """ % data.get('date_from')
            if data.get('date_to'):
                query += """ and l.date_order <= '%s' """ % data.get('date_to')
            query += """group by l.user_id,res_users.partner_id,res_partner.name,
                      l.partner_id,l.date_order,l.name,l.amount_total,l.notes,l.id"""
            self._cr.execute(query)
            report_by_order = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order)
        elif data.get('report_type') == 'report_by_order_detail':
            query = """ select l.name,l.date_order,l.partner_id,l.amount_total,
            l.notes, l.user_id,res_partner.name as partner,res_users.partner_id 
            as user_partner,sum(purchase_order_line.product_qty), 
            purchase_order_line.name as product, purchase_order_line.price_unit,
            purchase_order_line.price_subtotal,l.amount_total,
            purchase_order_line.product_id,product_product.default_code,
            (SELECT res_partner.name as salesman FROM res_partner WHERE 
            res_partner.id = res_users.partner_id)from purchase_order as l
            left join res_partner on l.partner_id = res_partner.id
            left join res_users on l.user_id = res_users.id
            left join purchase_order_line on l.id = purchase_order_line.order_id
            left join product_product on purchase_order_line.product_id = product_product.id 
            where 1=1 """
            if data.get('date_from'):
                query += """ and l.date_order >= '%s' """ % data.get('date_from')
            if data.get('date_to'):
                query += """ and l.date_order <= '%s' """ % data.get('date_to')
            query += """group by l.user_id,res_users.partner_id,res_partner.name,
            l.partner_id,l.date_order,l.name,l.amount_total,l.notes,
            purchase_order_line.name,purchase_order_line.price_unit,
            purchase_order_line.price_subtotal,l.amount_total,
            purchase_order_line.product_id,product_product.default_code"""
            self._cr.execute(query)
            report_by_order_details = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order_details)
        elif data.get('report_type') == 'report_by_product':
            query = """ select l.amount_total,sum(purchase_order_line.product_qty)
             as qty, purchase_order_line.name as product, purchase_order_line.price_unit,
            product_product.default_code,product_category.name from purchase_order
            as l left join purchase_order_line on l.id = purchase_order_line.order_id
            left join product_product on purchase_order_line.product_id = product_product.id
            left join product_template on purchase_order_line.product_id = product_template.id
            left join product_category on product_category.id = product_template.categ_id
            where 1=1   """
            if data.get('date_from'):
                query += """and l.date_order >= '%s' """ % data.get('date_from')
            if data.get('date_to'):
                query += """ and l.date_order <= '%s' """ % data.get('date_to')
            query += """group by l.amount_total,purchase_order_line.name,
                     purchase_order_line.price_unit,purchase_order_line.product_id,
                     product_product.default_code,product_template.categ_id,
                     product_category.name"""
            self._cr.execute(query)
            report_by_product = self._cr.dictfetchall()
            report_sub_lines.append(report_by_product)
        elif data.get('report_type') == 'report_by_categories':
            query = """ select product_category.name,sum(l.product_qty) as qty,
            sum(l.price_subtotal) as amount_total from purchase_order_line as l
            left join product_template on l.product_id = product_template.id
            left join product_category on product_category.id = product_template.categ_id
            left join purchase_order on l.order_id = purchase_order.id
            where 1=1 """
            if data.get('date_from'):
                query += """and pos_order.date_order >= '%s' """ % data.get(
                    'date_from')
            if data.get('date_to'):
                query += """ and pos_order.date_order <= '%s' """ % data.get(
                    'date_to')
            query += "group by product_category.name"
            self._cr.execute(query)
            report_by_categories = self._cr.dictfetchall()
            report_sub_lines.append(report_by_categories)
        elif data.get('report_type') == 'report_by_purchase_representative':
            query = """select res_partner.name,sum(purchase_order_line.product_qty)
            as qty,sum(purchase_order_line.price_subtotal) as amount,count(DISTINCT l.id)
            as order from purchase_order as l left join res_users on 
            l.user_id = res_users.id left join res_partner on 
            res_users.partner_id = res_partner.id left join purchase_order_line
            on l.id = purchase_order_line.order_id where 1=1 """
            if data.get('date_from'):
                query += """ and l.date_order >= '%s' """ % data.get('date_from')
            if data.get('date_to'):
                query += """ and l.date_order <= '%s' """ % data.get('date_to')
            query += "group by res_partner.name"
            self._cr.execute(query)
            report_by_purchase_representative = self._cr.dictfetchall()
            report_sub_lines.append(report_by_purchase_representative)
        elif data.get('report_type') == 'report_by_state':
            query = """select l.state,sum(purchase_order_line.product_qty) as 
            qty,sum(purchase_order_line.price_subtotal) as amount,
            count(DISTINCT l.id) as order from purchase_order as l
            left join res_users on l.user_id = res_users.id left join 
            res_partner on res_users.partner_id = res_partner.id
            left join purchase_order_line on l.id = purchase_order_line.order_id
            where 1=1 """
            if data.get('date_from'):
                query += """and so.date_order >= '%s' """ % data.get('date_from')
            if data.get('date_to'):
                query += """ and so.date_order <= '%s' """ % data.get('date_to')
            query += "group by l.state"
            self._cr.execute(query)
            report_by_state = self._cr.dictfetchall()
            report_sub_lines.append(report_by_state)
        return report_sub_lines

    @staticmethod
    def strip_html_tags(text):
        if not text:
            return ''
        return re.sub(r'<[^>]*>', '', text)

    def _get_report_values(self, data):
        """Get report values based on the provided data."""
        docs = data['model']
        if data.get('report_type'):
            report_res = self._get_report_sub_lines(data)[0]
        else:
            report_res = self._get_report_sub_lines(data)

        if isinstance(report_res, list):
            for row in report_res:
                if 'notes' in row:
                    row['notes'] = self.strip_html_tags(row['notes'])
        elif isinstance(report_res, dict):
            if 'notes' in report_res:
                report_res['notes'] = self.strip_html_tags(report_res['notes'])
        return {
            'doc_ids': self.ids,
            'docs': docs,
            'PURCHASE': report_res,
        }

    def get_purchase_xlsx_report(self, data, response, report_data, dfr_data):
        """ This function generates an XLSX report based on the provided data
        and report type. It writes the report data to the response
        object for download.
        Args:
            data (str): JSON data containing report filters.
            response (object): The response object used to send the XLSX file.
            report_data (str): JSON data containing the report data to be
            included in the XLSX.
            dfr_data: Data that doesn't appear to be used in this function."""
        report_data_main = json.loads(report_data)
        output = io.BytesIO()
        filters = json.loads(data)
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({
            'align': 'center', 'bold': True, 'font_size': '20px'})
        heading = workbook.add_format({'align': 'center', 'bold': True,
            'font_size': '10px', 'border': 1, 'border_color': 'black'})
        txt_l = workbook.add_format({
            'font_size': '10px', 'border': 1, 'bold': True})
        txt_normal = workbook.add_format({
            'font_size': '10px', 'border': 1})
        sheet.merge_range('A2:H3', 'Purchase Report', head)
        if filters.get('report_type') == 'report_by_order':
            sheet.merge_range('B5:C5', 'Report Type: ' +
                              'Report By Order', txt_l)

            if filters.get('date_from') and filters.get('date_to'):
                formatted_date_from = datetime.strptime(
                    filters['date_from'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                formatted_date_to = datetime.strptime(
                    filters['date_to'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                sheet.write('B6', 'Start Date:', txt_l)
                sheet.write('C6', formatted_date_from, txt_l)
                sheet.write('D6', 'End Date:', txt_l)
                sheet.write('E6', formatted_date_to, txt_l)

            sheet.write('A7', 'Order', heading)
            sheet.write('B7', 'Date Order', heading)
            sheet.write('C7', 'Customer', heading)
            sheet.write('D7', 'Purchase Representative', heading)
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
                row += 1
                sheet.write(row, col, rec_data['name'], txt_normal)
                sheet.write(row, col + 1, rec_data['date_order'], txt_normal)
                sheet.write(row, col + 2, rec_data['partner'], txt_normal)
                sheet.write(row, col + 3, rec_data['salesman'], txt_normal)
                sheet.write(row, col + 4, rec_data['sum'], txt_normal)
                sheet.write(row, col + 5, rec_data['amount_total'], txt_normal)
        if filters.get('report_type') == 'report_by_order_detail':
            sheet.merge_range('B5:C5', 'Report Type: ' +
                              'Report By Order Details', txt_l)

            if filters.get('date_from') and filters.get('date_to'):
                formatted_date_from = datetime.strptime(
                    filters['date_from'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                formatted_date_to = datetime.strptime(
                    filters['date_to'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                sheet.write('B6', 'Start Date:', txt_l)
                sheet.write('C6', formatted_date_from, txt_l)
                sheet.write('D6', 'End Date:', txt_l)
                sheet.write('E6', formatted_date_to, txt_l)

            sheet.write('A7', 'Order', heading)
            sheet.write('B7', 'Date Order', heading)
            sheet.write('C7', 'Customer', heading)
            sheet.write('D7', 'Purchase Representative', heading)
            sheet.write('E7', 'Product Code', heading)
            sheet.write('F7', 'Product Name', heading)
            sheet.write('G7', 'Price unit', heading)
            sheet.write('H7', 'Qty', heading)
            sheet.write('I7', 'Price Total', heading)
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
                row += 1
                sheet.write(row, col, rec_data['name'], txt_normal)
                sheet.write(row, col + 1, rec_data['date_order'], txt_normal)
                sheet.write(row, col + 2, rec_data['partner'], txt_normal)
                sheet.write(row, col + 3, rec_data['salesman'], txt_normal)
                sheet.write(row, col + 4, rec_data['default_code'], txt_normal)
                sheet.write(row, col + 5, rec_data['product'], txt_normal)
                sheet.write(row, col + 6, rec_data['price_unit'], txt_normal)
                sheet.write(row, col + 7, rec_data['sum'], txt_normal)
                sheet.write(row, col + 8, rec_data['amount_total'], txt_normal)
        if filters.get('report_type') == 'report_by_product':
            sheet.merge_range('B5:C5', 'Report Type: ' +
                              'Report By Product', txt_l)

            if filters.get('date_from') and filters.get('date_to'):
                formatted_date_from = datetime.strptime(
                    filters['date_from'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                formatted_date_to = datetime.strptime(
                    filters['date_to'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                sheet.write('B6', 'Start Date:', txt_l)
                sheet.write('C6', formatted_date_from, txt_l)
                sheet.write('D6', 'End Date:', txt_l)
                sheet.write('E6', formatted_date_to, txt_l)

            sheet.write('A7', 'Category', heading)
            sheet.write('B7', 'Product Code', heading)
            sheet.write('C7', 'Product Name', heading)
            sheet.write('D7', 'Qty', heading)
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
                row += 1
                sheet.write(row, col, rec_data['name'], txt_normal)
                sheet.write(row, col + 1, rec_data['default_code'], txt_normal)
                sheet.write(row, col + 2, rec_data['product'], txt_normal)
                sheet.write(row, col + 3, rec_data['qty'], txt_normal)
                sheet.write(row, col + 4, rec_data['amount_total'], txt_normal)
        if filters.get('report_type') == 'report_by_categories':
            sheet.merge_range('B5:C5', 'Report Type: ' +
                              'Report By Categories', txt_normal)

            if filters.get('date_from') and filters.get('date_to'):
                formatted_date_from = datetime.strptime(
                    filters['date_from'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                formatted_date_to = datetime.strptime(
                    filters['date_to'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                sheet.write('B6', 'Start Date:', txt_l)
                sheet.write('C6', formatted_date_from, txt_l)
                sheet.write('D6', 'End Date:', txt_l)
                sheet.write('E6', formatted_date_to, txt_l)

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
                row += 1
                sheet.write(row, col, rec_data['name'], txt_normal)
                sheet.write(row, col + 1, rec_data['qty'], txt_normal)
                sheet.write(row, col + 2, rec_data['amount_total'], txt_normal)
        if filters.get('report_type') == 'report_by_purchase_representative':
            sheet.merge_range('B5:C5', 'Report Type: ' +
                              'Report By Purchase Representative', txt_l)

            if filters.get('date_from') and filters.get('date_to'):
                formatted_date_from = datetime.strptime(
                    filters['date_from'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                formatted_date_to = datetime.strptime(
                    filters['date_to'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                sheet.write('B6', 'Start Date:', txt_l)
                sheet.write('C6', formatted_date_from, txt_l)
                sheet.write('D6', 'End Date:', txt_l)
                sheet.write('E6', formatted_date_to, txt_l)

            sheet.write('A7', 'Purchase Representative', heading)
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
                row += 1
                sheet.write(row, col, rec_data['name'], txt_normal)
                sheet.write(row, col + 1, rec_data['order'], txt_normal)
                sheet.write(row, col + 2, rec_data['qty'], txt_normal)
                sheet.write(row, col + 3, rec_data['amount'], txt_normal)
        if filters.get('report_type') == 'report_by_state':
            sheet.merge_range('B5:C5', 'Report Type: ' +
                              'Report By State', txt_l)

            if filters.get('date_from') and filters.get('date_to'):
                formatted_date_from = datetime.strptime(
                    filters['date_from'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                formatted_date_to = datetime.strptime(
                    filters['date_to'], '%Y-%m-%d %H:%M:%S').strftime(
                    '%d/%m/%y')
                sheet.write('B6', 'Start Date:', txt_l)
                sheet.write('C6', formatted_date_from, txt_l)
                sheet.write('D6', 'End Date:', txt_l)
                sheet.write('E6', formatted_date_to, txt_l)

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
                row += 1
                if rec_data['state'] == 'draft':
                    sheet.write(row, col, 'RFQ', txt_normal)
                elif rec_data['state'] == 'sent':
                    sheet.write(row, col, 'RFQ Sent', txt_normal)
                elif rec_data['state'] == 'purchase':
                    sheet.write(row, col, 'Purchase Order', txt_normal)
                sheet.write(row, col + 1, rec_data['order'], txt_normal)
                sheet.write(row, col + 2, rec_data['qty'], txt_normal)
                sheet.write(row, col + 3, rec_data['amount'], txt_normal)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
