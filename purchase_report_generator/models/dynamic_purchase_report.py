# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
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

    name = fields.Char(
        string="Purchase Report",
        default="Purchase Report",
        help="Name of the report"
    )
    date_from = fields.Datetime(
        string="Date From", help="Start date of report"
    )
    date_to = fields.Datetime(string="Date to", help="End date of report")
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
        self.env['purchase.order'].check_access('read')
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
        self.env['purchase.order'].check_access('read')
        report_data_main = json.loads(report_data)
        output = io.BytesIO()
        filters = json.loads(data)
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({
            'align': 'center', 'bold': True, 'font_size': '20px'})
        heading = workbook.add_format({
            'align': 'center', 'bold': True, 'font_size': '10px',
            'border': 1, 'border_color': 'black'
        })
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
            sheet.write('C7', 'Vendor', heading)
            sheet.write('D7', 'Purchase Representative', heading)
            sheet.write('E7', 'Total Qty', heading)
            sheet.write('F7', 'Amount Total', heading)
            row = 6
            col = 0
            sheet.set_column(0, 5, 15)
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
            sheet.write('C7', 'Vendor', heading)
            sheet.write('D7', 'Purchase Representative', heading)
            sheet.write('E7', 'Product Code', heading)
            sheet.write('F7', 'Product Name', heading)
            sheet.write('G7', 'Price Unit', heading)
            sheet.write('H7', 'Qty', heading)
            sheet.write('I7', 'Price Subtotal', heading)
            row = 6
            col = 0
            sheet.set_column(0, 8, 15)
            for rec_data in report_data_main:
                row += 1
                subtotal = (
                    rec_data.get('price_subtotal')
                    if rec_data.get('price_subtotal') is not None
                    else rec_data.get('amount_total')
                )
                sheet.write(row, col, rec_data['name'], txt_normal)
                sheet.write(row, col + 1, rec_data['date_order'], txt_normal)
                sheet.write(row, col + 2, rec_data['partner'], txt_normal)
                sheet.write(row, col + 3, rec_data['salesman'], txt_normal)
                sheet.write(row, col + 4, rec_data['default_code'], txt_normal)
                sheet.write(row, col + 5, rec_data['product'], txt_normal)
                sheet.write(row, col + 6, rec_data['price_unit'], txt_normal)
                sheet.write(row, col + 7, rec_data['sum'], txt_normal)
                sheet.write(row, col + 8, subtotal, txt_normal)
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
            row = 6
            col = 0
            sheet.set_column(0, 4, 15)
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
            row = 6
            col = 1
            sheet.set_column(1, 3, 15)
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
            row = 6
            col = 0
            sheet.set_column(0, 3, 15)
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
            sheet.write('D7', 'Total Amount', heading)
            row = 6
            col = 0
            sheet.set_column(0, 3, 15)
            for rec_data in report_data_main:
                row += 1
                if rec_data['state'] == 'draft':
                    sheet.write(row, col, 'RFQ', txt_normal)
                elif rec_data['state'] == 'sent':
                    sheet.write(row, col, 'RFQ Sent', txt_normal)
                elif rec_data['state'] == 'purchase':
                    sheet.write(row, col, 'Purchase Order', txt_normal)
                else:
                    sheet.write(row, col, rec_data['state'], txt_normal)
                sheet.write(row, col + 1, rec_data['order'], txt_normal)
                sheet.write(row, col + 2, rec_data['qty'], txt_normal)
                sheet.write(row, col + 3, rec_data['amount'], txt_normal)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def _get_report_values(self, data):
        """Get report values based on the provided data."""
        docs = data['model']
        if data.get('report_type'):
            report_res = self._get_report_sub_lines(data)[0]
        else:
            report_res = self._get_report_sub_lines(data)

        if isinstance(report_res, list):
            categ_names = {}
            for row in report_res:
                if 'note' in row and row['note']:
                    row['note'] = self.strip_html_tags(str(row['note']))
                for key, val in row.items():
                    if isinstance(val, dict):
                        env_lang = self.env.user.lang or 'en_US'
                        if env_lang in val:
                            row[key] = val[env_lang]
                        elif 'en_US' in val:
                            row[key] = val['en_US']
                        elif val:
                            row[key] = next(iter(val.values()))
                        else:
                            row[key] = ''

                if 'categ_id' in row:
                    cid = row.get('categ_id')
                    if cid:
                        if cid not in categ_names:
                            categ = self.env['product.category'].browse(cid)
                            categ_names[cid] = (
                                categ.display_name if categ.exists()
                                else row.get('name', '')
                            )
                        row['name'] = categ_names[cid]
                    else:
                        row['name'] = ''

                if 'product' in row and 'default_code' in row:
                    code = row.get('default_code')
                    name = row.get('product')
                    if code and name:
                        row['product'] = f"[{code}] {name}"
                    elif name:
                        row['product'] = name
                    elif code:
                        row['product'] = f"[{code}]"
                    else:
                        row['product'] = ""
        elif isinstance(report_res, dict):
            if 'note' in report_res and report_res['note']:
                report_res['note'] = self.strip_html_tags(
                    str(report_res['note'])
                )
            for key, val in report_res.items():
                if isinstance(val, dict):
                    env_lang = self.env.user.lang or 'en_US'
                    if env_lang in val:
                        report_res[key] = val[env_lang]
                    elif 'en_US' in val:
                        report_res[key] = val['en_US']
                    elif val:
                        report_res[key] = next(iter(val.values()))
                    else:
                        report_res[key] = ''
        return {
            'doc_ids': self.ids,
            'docs': docs,
            'PURCHASE': report_res,
        }

    def _get_report_sub_lines(self, data):
        """Function for get report value using sql query"""
        self.env['purchase.order'].check_access('read')
        self.env.flush_all()
        report_sub_lines = []
        company_ids = (
            self.env.context.get('allowed_company_ids')
            or self.env.company.ids
        )
        order_domain = [
            '|',
            ('company_id', '=', False),
            ('company_id', 'in', company_ids),
        ]
        if data.get('date_from'):
            order_domain.append(('date_order', '>=', data.get('date_from')))
        if data.get('date_to'):
            order_domain.append(('date_order', '<=', data.get('date_to')))
        allowed_orders = self.env['purchase.order'].search(order_domain)
        if not allowed_orders:
            report_sub_lines.append([])
            return report_sub_lines
        allowed_po_ids = tuple(allowed_orders.ids)

        if data.get('report_type') == 'report_by_order':
            query = """
                SELECT l.name, l.date_order, l.partner_id, l.amount_total,
                       l.note, l.user_id, res_partner.name AS partner,
                       res_users.partner_id AS user_partner,
                       SUM(purchase_order_line.product_qty),
                       l.id AS id,
                       (SELECT res_partner.name AS salesman
                          FROM res_partner
                         WHERE res_partner.id = res_users.partner_id)
                  FROM purchase_order AS l
                  LEFT JOIN res_partner ON l.partner_id = res_partner.id
                  LEFT JOIN res_users ON l.user_id = res_users.id
                  LEFT JOIN purchase_order_line
                         ON l.id = purchase_order_line.order_id
                 WHERE l.id IN %s
                 GROUP BY l.user_id, res_users.partner_id, res_partner.name,
                          l.partner_id, l.date_order, l.name, l.amount_total,
                          l.note, l.id
            """
            self.env.cr.execute(query, (allowed_po_ids,))
            report_by_order = self.env.cr.dictfetchall()
            report_sub_lines.append(report_by_order)
        elif data.get('report_type') == 'report_by_order_detail':
            query = """
                SELECT l.id AS id, l.name, l.date_order, l.partner_id,
                       l.amount_total AS order_amount_total,
                       SUM(purchase_order_line.price_subtotal)
                           AS amount_total,
                       SUM(purchase_order_line.price_subtotal)
                           AS price_subtotal,
                       l.note, l.user_id,
                       res_partner.name AS partner,
                       res_users.partner_id AS user_partner,
                       SUM(purchase_order_line.product_qty) AS sum,
                       SUM(purchase_order_line.product_qty) AS qty,
                       product_template.name AS product,
                       purchase_order_line.price_unit,
                       purchase_order_line.product_id,
                       product_product.default_code,
                       (SELECT res_partner.name AS salesman
                          FROM res_partner
                         WHERE res_partner.id = res_users.partner_id)
                  FROM purchase_order AS l
                  LEFT JOIN res_partner ON l.partner_id = res_partner.id
                  LEFT JOIN res_users ON l.user_id = res_users.id
                  LEFT JOIN purchase_order_line
                         ON l.id = purchase_order_line.order_id
                  LEFT JOIN product_product
                         ON purchase_order_line.product_id = product_product.id
                  LEFT JOIN product_template
                         ON product_product.product_tmpl_id =
                            product_template.id
                 WHERE l.id IN %s
                 GROUP BY l.id, l.user_id, res_users.partner_id,
                          res_partner.name, l.partner_id, l.date_order,
                          l.name, l.amount_total, l.note,
                          product_template.name,
                          purchase_order_line.price_unit,
                          purchase_order_line.product_id,
                          product_product.default_code
            """
            self.env.cr.execute(query, (allowed_po_ids,))
            report_by_order_details = self.env.cr.dictfetchall()
            report_sub_lines.append(report_by_order_details)
        elif data.get('report_type') == 'report_by_product':
            query = """
                SELECT SUM(purchase_order_line.price_subtotal)
                           AS amount_total,
                       SUM(purchase_order_line.product_qty) AS qty,
                       product_template.name AS product,
                       AVG(purchase_order_line.price_unit) AS price_unit,
                       product_product.default_code,
                       product_category.name AS name,
                       product_category.id AS categ_id
                  FROM purchase_order_line
                  JOIN purchase_order AS l
                         ON l.id = purchase_order_line.order_id
                  LEFT JOIN product_product
                         ON purchase_order_line.product_id = product_product.id
                  LEFT JOIN product_template
                         ON product_product.product_tmpl_id =
                            product_template.id
                  LEFT JOIN product_category
                         ON product_category.id = product_template.categ_id
                 WHERE l.id IN %s
                 GROUP BY product_template.name,
                          purchase_order_line.product_id,
                          product_product.default_code,
                          product_template.categ_id,
                          product_category.name,
                          product_category.id
            """
            self.env.cr.execute(query, (allowed_po_ids,))
            report_by_product = self.env.cr.dictfetchall()
            report_sub_lines.append(report_by_product)
        elif data.get('report_type') == 'report_by_categories':
            query = """
                SELECT product_category.name AS name,
                       product_category.id AS categ_id,
                       SUM(l.product_qty) AS qty,
                       SUM(l.price_subtotal) AS amount_total
                  FROM purchase_order_line AS l
                  LEFT JOIN product_product
                         ON l.product_id = product_product.id
                  LEFT JOIN product_template
                         ON product_product.product_tmpl_id =
                            product_template.id
                  LEFT JOIN product_category
                         ON product_category.id = product_template.categ_id
                  LEFT JOIN purchase_order
                         ON l.order_id = purchase_order.id
                 WHERE purchase_order.id IN %s
                 GROUP BY product_category.name, product_category.id
            """
            self.env.cr.execute(query, (allowed_po_ids,))
            report_by_categories = self.env.cr.dictfetchall()
            report_sub_lines.append(report_by_categories)
        elif data.get('report_type') == 'report_by_purchase_representative':
            query = """
                SELECT res_partner.name,
                       SUM(purchase_order_line.product_qty) AS qty,
                       SUM(purchase_order_line.price_subtotal) AS amount,
                       COUNT(DISTINCT l.id) AS order
                  FROM purchase_order AS l
                  LEFT JOIN res_users ON l.user_id = res_users.id
                  LEFT JOIN res_partner
                         ON res_users.partner_id = res_partner.id
                  LEFT JOIN purchase_order_line
                         ON l.id = purchase_order_line.order_id
                 WHERE l.id IN %s
                 GROUP BY res_partner.name
            """
            self.env.cr.execute(query, (allowed_po_ids,))
            report_by_purchase_representative = self.env.cr.dictfetchall()
            report_sub_lines.append(report_by_purchase_representative)
        elif data.get('report_type') == 'report_by_state':
            query = """
                SELECT l.state,
                       SUM(purchase_order_line.product_qty) AS qty,
                       SUM(purchase_order_line.price_subtotal) AS amount,
                       COUNT(DISTINCT l.id) AS order
                  FROM purchase_order AS l
                  LEFT JOIN res_users ON l.user_id = res_users.id
                  LEFT JOIN res_partner
                         ON res_users.partner_id = res_partner.id
                  LEFT JOIN purchase_order_line
                         ON l.id = purchase_order_line.order_id
                 WHERE l.id IN %s
                 GROUP BY l.state
            """
            self.env.cr.execute(query, (allowed_po_ids,))
            report_by_state = self.env.cr.dictfetchall()
            report_sub_lines.append(report_by_state)
        return report_sub_lines

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

    @staticmethod
    def strip_html_tags(text):
        if not text:
            return ''
        return re.sub(r'<[^>]*>', '', text)
