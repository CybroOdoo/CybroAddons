# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
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
###############################################################################
import io
import json
from odoo import api, fields, models
from odoo.exceptions import ValidationError
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DynamicPurchaseReport(models.Model):
    """Model for generating dynamic purchase reports"""
    _name = "dynamic.purchase.report"
    _description = 'Dynamic Purchase Report'

    purchase_report = fields.Char(
        string="Purchase Report", help="Purchase Report"
    )
    date_from = fields.Datetime(
        string="Date From", help="From which date report needed"
    )
    date_to = fields.Datetime(
        string="Date to", help="Till which date report needs to print"
    )
    report_type = fields.Selection([
        ('report_by_order', 'Report By Order'),
        ('report_by_order_detail', 'Report By Order Detail'),
        ('report_by_product', 'Report By Product'),
        ('report_by_categories', 'Report By Categories'),
        ('report_by_purchase_representative',
         'Report By Purchase Representative'),
        ('report_by_state', 'Report By State')], default='report_by_order',
        string="Report Type",
        help="Choose the report type need to be printed"
    )

    @api.model
    def purchase_report(self, option):
        """
        Generate a dynamic purchase report.
        """
        report_values = self.env['dynamic.purchase.report'].browse(option)
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
        """Get the selected filter type for the report."""
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
        """Get filter data for the specified report configuration."""
        return {
            'report_type': self.env[
                'dynamic.purchase.report'].browse(option).report_type
        }

    @api.model
    def create(self, vals):
        """Override the default create method to create a new dynamic purchase
         report record."""
        return super(DynamicPurchaseReport, self).create(vals)

    def write(self, vals):
        """Override the default write method to update the field values of the
         dynamic purchase report record."""
        return super(DynamicPurchaseReport, self).write(vals)

    def _get_report_sub_lines(self, data, report, date_from, date_to):
        """Getting data for report lines"""
        report_sub_lines = []
        if data.get('report_type') == 'report_by_order':
            query = '''
            select l.name,l.date_order,l.partner_id,l.amount_total,
            l.notes,l.user_id,res_partner.name as partner,
            res_users.partner_id as user_partner,
            sum(purchase_order_line.product_qty),l.id as id,
            (SELECT res_partner.name as salesman FROM
            res_partner WHERE res_partner.id = res_users.partner_id)
            from purchase_order as l
            left join res_partner on l.partner_id = res_partner.id
            left join res_users on l.user_id = res_users.id
            left join purchase_order_line on l.id =
            purchase_order_line.order_id
            '''
            term = 'Where '
            if data.get('date_from') and data.get('date_to') and \
                    data.get('date_from') > data.get('date_to'):
                raise ValidationError('Start Date cannot be greater than '
                                      'End Date')
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by l.user_id,res_users.partner_id," \
                     "res_partner.name,l.partner_id,l.date_order,l.name," \
                     "l.amount_total,l.notes,l.id"
            self._cr.execute(query)
            report_by_order = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order)
        elif data.get('report_type') == 'report_by_order_detail':
            query = '''
            select l.name,l.date_order,l.partner_id,l.amount_total,
            l.notes,l.user_id,res_partner.name as partner,
            res_users.partner_id as user_partner,
            sum(purchase_order_line.product_qty),
            purchase_order_line.name as product,
            purchase_order_line.price_unit,purchase_order_line.price_subtotal,
            l.amount_total,purchase_order_line.product_id,
            product_product.default_code,
            (SELECT res_partner.name as salesman FROM res_partner
            WHERE res_partner.id = res_users.partner_id)
            from purchase_order as l
            left join res_partner on l.partner_id = res_partner.id
            left join res_users on l.user_id = res_users.id
            left join purchase_order_line on l.id =
            purchase_order_line.order_id
            left join product_product on purchase_order_line.product_id =
            product_product.id
            '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by l.user_id,res_users.partner_id," \
                     "res_partner.name,l.partner_id,l.date_order," \
                     "l.name,l.amount_total,l.notes," \
                     "purchase_order_line.name," \
                     "purchase_order_line.price_unit," \
                     "purchase_order_line.price_subtotal,l.amount_total," \
                     "purchase_order_line.product_id," \
                     "product_product.default_code"
            self._cr.execute(query)
            report_by_order_details = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order_details)
        elif data.get('report_type') == 'report_by_product':
            query = '''
            select l.amount_total,sum(purchase_order_line.product_qty) as qty,
            purchase_order_line.name as product,
            purchase_order_line.price_unit,product_product.default_code,
            product_category.name
            from purchase_order as l
            left join purchase_order_line on l.id =
            purchase_order_line.order_id
            left join product_product on purchase_order_line.product_id =
            product_product.id
            left join product_template on purchase_order_line.product_id =
            product_template.id
            left join product_category on product_category.id =
            product_template.categ_id
            '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by l.amount_total,purchase_order_line.name," \
                     "purchase_order_line.price_unit," \
                     "purchase_order_line.product_id," \
                     "product_product.default_code," \
                     "product_template.categ_id,product_category.name"
            self._cr.execute(query)
            report_by_product = self._cr.dictfetchall()
            report_sub_lines.append(report_by_product)
        elif data.get('report_type') == 'report_by_categories':
            query = '''
            select product_category.name,sum(l.product_qty) as qty,
            sum(l.price_subtotal) as amount_total
            from purchase_order_line as l
            left join product_template on l.product_id = product_template.id
            left join product_category on product_category.id =
            product_template.categ_id
            left join purchase_order on l.order_id = purchase_order.id
            '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where pos_order.date_order >= '%s' " % data.get(
                    'date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "pos_order.date_order <= '%s' " % data.get(
                    'date_to')
            query += "group by product_category.name"
            self._cr.execute(query)
            report_by_categories = self._cr.dictfetchall()
            report_sub_lines.append(report_by_categories)
        elif data.get('report_type') == 'report_by_purchase_representative':
            query = '''
            select res_partner.name,sum(purchase_order_line.product_qty) as
            qty,sum(purchase_order_line.price_subtotal) as amount,count(l.id)
            as order from purchase_order as l
            left join res_users on l.user_id = res_users.id
            left join res_partner on res_users.partner_id = res_partner.id
            left join purchase_order_line on l.id =
            purchase_order_line.order_id
            '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by res_partner.name"
            self._cr.execute(query)
            report_by_purchase_representative = self._cr.dictfetchall()
            report_sub_lines.append(report_by_purchase_representative)
        elif data.get('report_type') == 'report_by_state':
            query = '''
            select l.state,sum(purchase_order_line.product_qty) as
            qty,sum(purchase_order_line.price_subtotal) as amount,count(l.id)
            as order from purchase_order as l
            left join res_users on l.user_id = res_users.id
            left join res_partner on res_users.partner_id = res_partner.id
            left join purchase_order_line on l.id =
            purchase_order_line.order_id
            '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where so.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "so.date_order <= '%s' " % data.get('date_to')
            query += "group by l.state"
            self._cr.execute(query)
            report_by_state = self._cr.dictfetchall()
            report_sub_lines.append(report_by_state)
        return report_sub_lines

    def _get_report_values(self, data):
        """Get data for the specified type of report lines."""
        docs = data['model']
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        if data['report_type'] == 'report_by_order_detail':
            report = ['Report By Order Detail']
        elif data['report_type'] == 'report_by_product':
            report = ['Report By Product']
        elif data['report_type'] == 'report_by_categories':
            report = ['Report By Categories']
        elif data['report_type'] == 'report_by_purchase_representative':
            report = ['Report By Purchase Representative']
        elif data['report_type'] == 'report_by_state':
            report = ['Report By State']
        else:
            report = ['Report By Order']
        if data.get('report_type'):
            report_res = \
                self._get_report_sub_lines(data, report, date_from, date_to)[0]
        else:
            report_res = self._get_report_sub_lines(data, report, date_from,
                                                    date_to)
        return {
            'doc_ids': self.ids,
            'docs': docs,
            'PURCHASE': report_res,
        }

    def get_purchase_xlsx_report(self, data, response, report_data, dfr_data):
        """Generate an XLSX report with purchase data based on provided
         filters."""
        report_data_main = json.loads(report_data)
        output = io.BytesIO()
        filters = json.loads(data)
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 2,
             'border_color': 'black'})
        txt_l = workbook.add_format(
            {'font_size': '10px', 'border': 1, 'bold': True})
        sheet.merge_range('A2:H3', 'Purchase Report', head)
        if filters.get('report_type') == 'report_by_order':
            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)
            sheet.write('A7', 'Order', heading)
            sheet.write('B7', 'Date Order', heading)
            sheet.write('C7', 'Customer', heading)
            sheet.write('D7', 'Purchase Representative', heading)
            sheet.write('E7', 'Total Qty', heading)
            sheet.write('F7', 'Amount Total', heading)
            if report_data_main:
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
                    sheet.write(row, col, rec_data['name'], txt_l)
                    sheet.write(row, col + 1, rec_data['date_order'], txt_l)
                    sheet.write(row, col + 2, rec_data['partner'], txt_l)
                    sheet.write(row, col + 3, rec_data['salesman'], txt_l)
                    sheet.write(row, col + 4, rec_data['sum'], txt_l)
                    sheet.write(row, col + 5, rec_data['amount_total'], txt_l)
        if filters.get('report_type') == 'report_by_order_detail':
            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)
            sheet.write('A7', 'Order', heading)
            sheet.write('B7', 'Date Order', heading)
            sheet.write('C7', 'Customer', heading)
            sheet.write('D7', 'Purchase Representative', heading)
            sheet.write('E7', 'Product Code', heading)
            sheet.write('F7', 'Product Name', heading)
            sheet.write('G7', 'Price unit', heading)
            sheet.write('H7', 'Qty', heading)
            sheet.write('I7', 'Price Total', heading)
            if report_data_main:
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
                    sheet.write(row, col, rec_data['name'], txt_l)
                    sheet.write(row, col + 1, rec_data['date_order'], txt_l)
                    sheet.write(row, col + 2, rec_data['partner'], txt_l)
                    sheet.write(row, col + 3, rec_data['salesman'], txt_l)
                    sheet.write(row, col + 4, rec_data['default_code'], txt_l)
                    sheet.write(row, col + 5, rec_data['product'], txt_l)
                    sheet.write(row, col + 6, rec_data['price_unit'], txt_l)
                    sheet.write(row, col + 7, rec_data['sum'], txt_l)
                    sheet.write(row, col + 8, rec_data['amount_total'], txt_l)
        if filters.get('report_type') == 'report_by_product':
            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)
            sheet.write('A7', 'Category', heading)
            sheet.write('B7', 'Product Code', heading)
            sheet.write('C7', 'Product Name', heading)
            sheet.write('D7', 'Qty', heading)
            sheet.write('E7', 'Amount Total', heading)
            if report_data_main:
                row = 6
                col = 0
                sheet.set_column(3, 0, 15)
                sheet.set_column(4, 1, 15)
                sheet.set_column(5, 2, 15)
                sheet.set_column(6, 3, 15)
                sheet.set_column(7, 4, 15)
                for rec_data in report_data_main:
                    row += 1
                    sheet.write(row, col, rec_data['name'], txt_l)
                    sheet.write(row, col + 1, rec_data['default_code'], txt_l)
                    sheet.write(row, col + 2, rec_data['product'], txt_l)
                    sheet.write(row, col + 3, rec_data['qty'], txt_l)
                    sheet.write(row, col + 4, rec_data['amount_total'], txt_l)
        if filters.get('report_type') == 'report_by_categories':
            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)
            sheet.write('B7', 'Category', heading)
            sheet.write('C7', 'Qty', heading)
            sheet.write('D7', 'Amount Total', heading)
            if report_data_main:
                row = 6
                col = 1
                sheet.set_column(3, 1, 15)
                sheet.set_column(4, 2, 15)
                sheet.set_column(5, 3, 15)
                for rec_data in report_data_main:
                    row += 1
                    sheet.write(row, col, rec_data['name'], txt_l)
                    sheet.write(row, col + 1, rec_data['qty'], txt_l)
                    sheet.write(row, col + 2, rec_data['amount_total'], txt_l)
        if filters.get('report_type') == 'report_by_purchase_representative':
            sheet.merge_range('B5:D5', 'Report Type: ' +
                              filters.get('report_type'), txt_l)
            sheet.write('A7', 'Purchase Representative', heading)
            sheet.write('B7', 'Total Order', heading)
            sheet.write('C7', 'Total Qty', heading)
            sheet.write('D7', 'Total Amount', heading)
            if report_data_main:
                row = 6
                col = 0
                sheet.set_column(3, 0, 15)
                sheet.set_column(4, 1, 15)
                sheet.set_column(5, 2, 15)
                sheet.set_column(6, 3, 15)
                for rec_data in report_data_main:
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
            if report_data_main:
                row = 6
                col = 0
                sheet.set_column(3, 0, 15)
                sheet.set_column(4, 1, 15)
                sheet.set_column(5, 2, 15)
                sheet.set_column(6, 3, 15)
                for rec_data in report_data_main:
                    row += 1
                    if rec_data['state'] == 'draft':
                        sheet.write(row, col, 'Quotation', txt_l)
                    elif rec_data['state'] == 'sent':
                        sheet.write(row, col, 'Quotation Sent', txt_l)
                    elif rec_data['state'] == 'purchase':
                        sheet.write(row, col, 'Purchase Order', txt_l)
                    sheet.write(row, col + 1, rec_data['order'], txt_l)
                    sheet.write(row, col + 2, rec_data['qty'], txt_l)
                    sheet.write(row, col + 3, rec_data['amount'], txt_l)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
