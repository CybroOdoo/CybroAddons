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
import base64
import secrets
import string
import csv
from io import StringIO
from odoo import api, fields, models


class ProductDataFeed(models.Model):
    """Data feed model for managing and generating product data feeds.
    This class represents a product data feed, which can be used to export
    product information in a specific format. It inherits from 'mail.thread'
    and 'mail.activity.mixin' to provide messaging and activity tracking
    capabilities."""
    _name = 'product.data.feed'
    _description = 'Product Data Feed'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', help='Name of the feed', copy=False,
                       required=True)
    url_link = fields.Char(string='Link', help='Data feed download link',
                           compute='_compute_url_link')
    is_token = fields.Boolean(string='Use Token',
                              help='Use token or Not for the '
                                   'security')
    access_token = fields.Char(string='Access Token',
                               help='Access Token of the feed',
                               compute='_compute_access_token')
    website_id = fields.Many2one('website', string='Websites',
                                 help='Allow this data feed for the selected '
                                      'websites.Allow for all if not set ')
    format = fields.Char(string='File Formate',
                         help='The file formate of the data feed.',
                         default='CSV', readonly=True)
    is_file_name = fields.Boolean(string='File Name',
                                  help='Enabled the file name')
    name_show = fields.Char(string='File Name', help='Show the file name',
                            compute='_compute_name_show')
    use_model = fields.Selection(
        [('Product', 'Product'), ('Product Variant', 'Product Variant')],
        string='Use Model', help='Used model of the product feed',
        default='Product', required=True)
    used_model = fields.Char(string='Used Model', help='Model')
    item_filter = fields.Char(string='Item Filter', help='The model domain to'
                                                         ' filter for the feed')
    feed_columns_line_ids = fields.One2many('product.data.feed.columns',
                                            'data_feed_columns_id',
                                            string='Columns',
                                            help='Feed column line',
                                            readonly=True,)
    columns_count = fields.Integer(string='Columns Count',
                                   help='Total number of columns used this '
                                        'feed',
                                   compute='_compute_columns_count')

    def generate_formatted_file_content(self, columns, item_filter):
        """Generate formatted content for a file based on specified columns
        and an item filter.This method applies the provided filter criteria to
        fetch relevant items from the environment, and then generates formatted
        rows of values for the specified columns for each item."""
        # Apply the filter criteria and fetch the relevant items
        filtered_items = self.env[self.used_model].search(item_filter)
        formatted_rows = []
        # Iterate over each item and generate a row of values
        for item in filtered_items:
            row = []
            value = ''
            for column in columns:
                if column.type == 'Model Field':
                    # Access the field value directly
                    model_value = getattr(item, column.value_id.name, '')
                    if model_value:
                        value = model_value
                    else:
                        value = ''

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
                    elif column.special_type == 'image_link':
                        value = item.image_1920
                    elif column.special_type == 'price_tax':
                        if item.taxes_id:
                            value = (item.list_price * (
                                        item.taxes_id.amount / 100) +
                                     item.list_price)
                        else:
                            value = 0.0
                elif column.type == 'Text':
                    value = column.value
                elif column.type == 'Value':
                    value = column.field_value_id.value
                else:
                    value = column.value
                if value:
                    row.append(value)
            formatted_rows.append(row)
        return formatted_rows

    def action_download_doc(self):
        """Download the catalog"""
        columns = self.feed_columns_line_ids
        item_filter = eval(self.item_filter) if self.item_filter else []
        formatted_file_content = self.generate_formatted_file_content(
            columns, item_filter)
        # Create a CSV content string
        csv_content = StringIO()
        csv_writer = csv.writer(csv_content)
        column_header = [column.name for column in columns]
        csv_writer.writerow(column_header)
        for row in formatted_file_content:
            csv_writer.writerow(row)
        encoded_content = csv_content.getvalue().encode('utf-8')
        # Close the StringIO buffer
        csv_content.close()
        attachment = self.env['ir.attachment'].create({
            'name': self.name_show if self.name_show else 'feed',
            'type': 'binary',
            'datas': base64.b64encode(encoded_content),
            'res_model': self.used_model,
            'res_id': self.id,
            'mimetype': 'text/csv'
        })
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': f"/web/content/{attachment.id}?download=true"
        }

    def action_product_items(self):
        """Open the product item list"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Feed Items',
            'view_mode': 'tree,form',
            'res_model': self.used_model,
            'domain': self.item_filter,
            'context': self.env.context,
        }

    def action_columns_creation(self):
        """Create the columns for feed."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Columns',
            'view_mode': 'tree,form',
            'res_model': 'product.data.feed.columns',
            'context': {
                'default_feed_id': self.id,
                'default_data_feed_columns_id': self.id,
            },
            'domain': [('feed_id', '=', self.id)]
        }

    @api.depends('access_token')
    def _compute_access_token(self):
        """Update the access token when enabling the token boolean field"""
        access_tokens = secrets.token_urlsafe(27)
        self.write({'access_token': access_tokens})

    def action_refresh_token(self):
        """Refresh and generate new token"""
        access_tokens = secrets.token_urlsafe(
            27)  # 27 bytes gives you 36 characters
        self.write({'access_token': access_tokens})

    @api.depends('name_show')
    def _compute_name_show(self):
        """Generate the random name when enabling the file_name"""
        prefix = "feed-"
        random_length = 4
        random_chars = ''.join(
            secrets.choice(string.ascii_letters + string.digits) for _ in
            range(random_length))
        random_name = prefix + random_chars
        self.write({'name_show': random_name})

    @api.onchange('use_model')
    def _onchange_use_model(self):
        """When changing the use_model it update the model into used_model"""
        if self.use_model == 'Product':
            self.write({'used_model': 'product.template'})
        else:
            self.write({'used_model': 'product.product'})

    @api.depends('format', 'name_show', 'is_token')
    def _compute_url_link(self):
        """Compute the downloading link"""
        for feed in self:
            base_url = self.env['ir.config_parameter'].get_param(
                'web.base.url') + '/product_data'
            if feed.is_token and feed.is_file_name:
                feed.url_link = f'{base_url}/{self.id}/{feed.name_show}.{feed.format}?access_token={feed.access_token}'
            elif feed.is_file_name:
                feed.url_link = f'{base_url}/{self.id}/{feed.name_show}.{feed.format}'
            elif feed.is_token:
                feed.url_link = f'{base_url}/{self.id}/feed.{feed.format}?access_token={feed.access_token}'
            else:
                feed.url_link = f'{base_url}/{self.id}/feed.{feed.format}'

    def _compute_columns_count(self):
        """Calculate the total number of column count of the current feed"""
        for rec in self:
            if rec.ids:
                rec.columns_count = self.env[
                    'product.data.feed.columns'].search_count(
                    [('feed_id', '=', rec.id)])
            else:
                rec.columns_count = 0
