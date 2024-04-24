# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina P (odoo@cybrosys.com)
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
import csv
from six import StringIO
from odoo import http
from odoo.http import request


class ProductData(http.Controller):
    """This controller handle for downloading the catalog csv file"""
    def generate_formatted_file_content(self, columns, item_filter, record):
        """Generating the file content"""
        # Apply the filter criteria and fetch the relevant items
        filtered_items = request.env[record.used_model].search(item_filter)
        formatted_rows = []
        # Iterate over each item and generate a row of values
        for item in filtered_items:
            row = []
            for column in columns:
                if column.type == 'Model Field':
                    # Access the field value directly
                    value = getattr(item, column.value_id.name, '')
                elif column.type == 'Special':
                    if column.special_type == 'product_availability':
                        # Access the product's on-hand quantity
                        on_hand_qty = item.qty_available
                        # Set value based on on-hand quantity
                        if on_hand_qty == 0:
                            value = 'out of stock'
                        else:
                            value = 'in stock'
                    elif column.special_type == 'qty':
                        value = item.qty_available
                    elif column.special_type == 'product_price':
                        value = item.standard_price
                    elif column.special_type == 'disc_price':
                        value = item.list_price
                    elif column.special_type == 'price_without_tax':
                        value = item.list_price
                    elif column.special_type == 'price_currency':
                        value = self.currency_id.name
                elif column.type == 'Text':
                    value = column.value
                elif column.type == 'Value':
                    value = column.field_value_id.column_name
                else:
                    value = column.value
                row.append(value)
            formatted_rows.append(row)
        return formatted_rows

    @http.route(['/product_data/<int:id>/<name>',
                 '/product_data/<name>'
                 ], type="http",
                auth='public')
    def product_data(self, id, name):
        """Making the product data into a CSV formate."""
        record = request.env['product.data.feed'].sudo().browse(id)
        column_ids = record.feed_columns_line_ids
        item_filter = eval(record.item_filter) if record.item_filter else []
        formatted_file_content = self.generate_formatted_file_content(
            column_ids, item_filter, record)
        csv_content = StringIO()
        csv_writer = csv.writer(csv_content)
        column_header = [column.name for column in column_ids]
        csv_writer.writerow(column_header)
        for row in formatted_file_content:
            csv_writer.writerow(row)
        # Get CSV content as a string
        csv_string = csv_content.getvalue()
        csv_content.close()
        headers = [
            ('Content-Type', 'text/csv'),
            ('Content-Disposition', http.content_disposition(name + '.csv')),
        ]
        return request.make_response(csv_string, headers=headers)
