# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.

###############################################################################
import io
import json
from odoo import api, fields, models
from odoo.tools import SQL

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


# pylint: disable=no-wizard-in-models
class DynamicInventoryReport(models.TransientModel):
    """Transient model for generating dynamic inventory reports.
    This class represents a wizard model for generating dynamic inventory
    reports based on various criteria. It provides methods for creating,
    updating, and generating reports with options like report type, date range,
    and filters."""
    _name = "dynamic.inventory.report"
    _description = "All in one inventory report"

    purchase_report = fields.Char(string="Inventory Report",
                                  help="The name or title of the dynamic "
                                       "inventory report.")
    date_from = fields.Datetime(help="The starting date")
    date_to = fields.Datetime(string="Date to", help="The ending date")
    report_type = fields.Selection([
        ('report_by_transfers', 'Report By Transfers'),
        ('report_by_categories', 'Report By Categories'),
        ('report_by_warehouse', 'Report By Warehouse'),
        ('report_by_location', 'Report By Location')],
        default='report_by_transfers', help="The type of dynamic inventory "
                                            "report to generate.")

    @api.model
    def inventory_report(self, option):
        """Generate and return an inventory report.
           Args:
               option (list): A list containing the report options.
           Returns:
               dict: A dictionary containing report data."""
        report_values = self.env['dynamic.inventory.report'].search(
            [('id', '=', option[0])])
        data = {
            'report_type': report_values.report_type,
            'model': self,
            'company_id': self.env.company.id,
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
        lines = self._get_report_values(data).get('INVENTORY')
        return {
            'name': "Inventory Orders",
            'type': 'ir.actions.client',
            'tag': 'inv_r',
            'orders': data,
            'filters': filters,
            'report_lines': lines,
        }

    def get_filter(self, option):
        """Get filters for the inventory report.
           Args:
               option (list): A list containing the report options.
           Returns:
               dict: A dictionary containing filter data for the report."""
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
        """Get filter data for the inventory report.
            Args:
                option (list): A list containing the report options.
            Returns:
                dict: A dictionary containing filter data for the report."""
        r = self.env['dynamic.inventory.report'].search(
            [('id', '=', option[0])])
        default_filters = {}
        filter_dict = {
            'report_type': r.report_type,
        }
        filter_dict.update(default_filters)
        return filter_dict


    def _get_report_sub_lines(self, data, report, date_from, date_to):
        """Get sub-lines of the inventory report.
            Args:
                data (dict): Data for generating the report.
                report (str): The type of report.
                date_from (datetime): Start date for filtering.
                date_to (datetime): End date for filtering.
            Returns:
                list: List of sub-lines for the inventory report."""
        report_sub_lines = []
        company_ids = tuple(self.env.companies.ids) or (self.env.company.id,)
        if data.get('report_type') == 'report_by_transfers':
            where_clauses = [
                SQL(
                    "(l.company_id IS NULL OR l.company_id IN %s)",
                    company_ids,
                )
            ]
            if data.get('date_from'):
                where_clauses.append(
                    SQL("l.scheduled_date >= %s", data.get('date_from'))
                )
            if data.get('date_to'):
                where_clauses.append(
                    SQL("l.scheduled_date <= %s", data.get('date_to'))
                )
            where_sql = (
                SQL(" WHERE %s", SQL(" AND ").join(where_clauses))
                if where_clauses
                else SQL()
            )
            query = SQL(
                """SELECT l.name, l.partner_id, l.scheduled_date, l.origin,
                          l.company_id, l.state, res_partner.name AS partner,
                          res_company.name AS company, l.id AS id
                     FROM stock_picking AS l
                LEFT JOIN res_partner ON l.partner_id = res_partner.id
                LEFT JOIN res_company ON l.company_id = res_company.id
                   %s""",
                where_sql,
            )
            self.env.cr.execute(query)
            report_by_order = self.env.cr.dictfetchall()
            report_sub_lines.append(report_by_order)
        elif data.get('report_type') == 'report_by_categories':
            where_clauses = [
                SQL(
                    "(stock_quant.company_id IS NULL "
                    "OR stock_quant.company_id IN %s)",
                    company_ids,
                )
            ]
            if data.get('date_from'):
                where_clauses.append(
                    SQL("stock_quant.create_date >= %s", data.get('date_from'))
                )
            if data.get('date_to'):
                where_clauses.append(
                    SQL("stock_quant.create_date <= %s", data.get('date_to'))
                )
            where_sql = (
                SQL(" WHERE %s", SQL(" AND ").join(where_clauses))
                if where_clauses
                else SQL()
            )
            query = SQL(
                """SELECT product_product.standard_price AS value_float,
                          product_template.name,
                          product_template.create_date,
                          product_template.categ_id,
                          product_product.id,
                          stock_quant.quantity,
                          product_category.name AS category,
                          stock_location.complete_name AS location
                     FROM product_product
               INNER JOIN product_template
                       ON product_product.product_tmpl_id = product_template.id
               INNER JOIN stock_quant
                       ON product_product.id = stock_quant.product_id
               INNER JOIN stock_location
                       ON stock_quant.location_id = stock_location.id
                LEFT JOIN product_category
                       ON product_category.id = product_template.categ_id
                   %s""",
                where_sql,
            )
            self.env.cr.execute(query)
            report_by_order_details = self.env.cr.dictfetchall()
            cid = self.env.company.id
            cid_str = str(cid)
            for row in report_by_order_details:
                val = row.get('value_float')
                if isinstance(val, dict):
                    cost = val.get(cid_str) or val.get(cid) or (
                        list(val.values())[0] if val else 0.0
                    )
                    row['cost'] = cost
                elif val is not None:
                    row['cost'] = val
                else:
                    row['cost'] = 0.0
            report_sub_lines.append(report_by_order_details)
        elif data.get('report_type') == 'report_by_warehouse':
            where_clauses = [
                SQL(
                    "(l.company_id IS NULL OR l.company_id IN %s)",
                    company_ids,
                )
            ]
            if data.get('date_from'):
                where_clauses.append(
                    SQL("l.write_date >= %s", data.get('date_from'))
                )
            if data.get('date_to'):
                where_clauses.append(
                    SQL("l.write_date <= %s", data.get('date_to'))
                )
            where_sql = (
                SQL(" WHERE %s", SQL(" AND ").join(where_clauses))
                if where_clauses
                else SQL()
            )
            query = SQL(
                """SELECT l.name, l.company_id, l.view_location_id,
                          l.reception_route_id AS route, l.write_date,
                          res_company.name AS company,
                          stock_location.name AS location,
                          stock_route.name AS route
                     FROM stock_warehouse AS l
                LEFT JOIN res_company ON res_company.id = l.company_id
                LEFT JOIN stock_location
                       ON stock_location.id = l.view_location_id
                LEFT JOIN stock_route ON stock_route.id = l.reception_route_id
                   %s""",
                where_sql,
            )
            self.env.cr.execute(query)
            report_by_product = self.env.cr.dictfetchall()
            report_sub_lines.append(report_by_product)
        elif data.get('report_type') == 'report_by_location':
            where_clauses = [
                SQL(
                    "(l.company_id IS NULL OR l.company_id IN %s)",
                    company_ids,
                )
            ]
            if data.get('date_from'):
                where_clauses.append(
                    SQL("l.create_date >= %s", data.get('date_from'))
                )
            if data.get('date_to'):
                where_clauses.append(
                    SQL("l.create_date <= %s", data.get('date_to'))
                )
            where_sql = (
                SQL(" WHERE %s", SQL(" AND ").join(where_clauses))
                if where_clauses
                else SQL()
            )
            query = SQL(
                """SELECT l.complete_name, l.usage AS location_type,
                          l.create_date, l.company_id,
                          res_company.name AS company
                     FROM stock_location AS l
                LEFT JOIN res_company ON res_company.id = l.company_id
                   %s""",
                where_sql,
            )
            self.env.cr.execute(query)
            report_by_categories = self.env.cr.dictfetchall()
            report_sub_lines.append(report_by_categories)
        return report_sub_lines

    def _get_report_values(self, data):
        """Get the values for the inventory report.
           Args:
               data (dict): Data for generating the report.
           Returns:
               dict: Dictionary containing report data."""
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
        sub_lines = self._get_report_sub_lines(data, report, date_from, date_to)
        if data.get('report_type'):
            report_res = sub_lines[0] if sub_lines else []
        else:
            report_res = sub_lines
        return {
            'doc_ids': self.ids,
            'docs': docs,
            'INVENTORY': report_res,
        }

    def get_inventory_xlsx_report(self, data, response, report_data, dfr_data):
        """Generate an XLSX report for the inventory data.
            Args:
                data (str): JSON data for the report.
                response (object): Response object for the XLSX report.
                report_data (str): JSON data for the report.
                dfr_data (str): JSON data for DynamicInventoryReport."""
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
        sheet.merge_range('A2:F3', 'Inventory Report', head)
        if filters.get('report_type') == 'report_by_transfers':
            sheet.merge_range('A5:D5', 'Report Type: ' +
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
            sheet.write('E7', 'Location', heading)
            sheet.write('F7', 'On Hand Qty', heading)
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
                sheet.write(row, col, rec_data['category'], txt_l)
                sheet.write(row, col + 1, rec_data['name']['en_US'], txt_l)
                sheet.write(row, col + 2, rec_data['create_date'], txt_l)
                if rec_data.get('value_float'):
                    val = rec_data['value_float']
                    cid_str = str(self.env.company.id)
                    if isinstance(val, dict):
                        value = val.get(cid_str) or (
                            list(val.values())[0] if val else 0.0
                        )
                    else:
                        value = val
                    sheet.write(row, col + 3, value, txt_l)
                sheet.write(row, col + 4, rec_data['location'], txt_l)
                sheet.write(row, col + 5, rec_data['quantity'], txt_l)
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
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['write_date'], txt_l)
                sheet.write(row, col + 2, rec_data['company'], txt_l)
                sheet.write(row, col + 3, rec_data['location'], txt_l)
                sheet.write(row, col + 4, rec_data['route']['en_US'], txt_l)
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
                row += 1
                sheet.write(row, col, rec_data['complete_name'], txt_l)
                sheet.write(row, col + 1, rec_data['location_type'], txt_l)
                sheet.write(row, col + 2, rec_data['create_date'], txt_l)
                sheet.write(row, col + 3, rec_data['company'], txt_l)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
