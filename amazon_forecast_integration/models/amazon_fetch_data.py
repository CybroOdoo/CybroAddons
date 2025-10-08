# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
import xmlrpc.client
from odoo import fields, models, _


class AmazonFetchData(models.Model):
    """Class for fetching the data from our database"""
    _name = "amazon.fetch.data"
    _description = "To Fetch Data"
    _rec_name = "db_name"

    url = fields.Char(string="URL", required=True,
                      help="Provide the URL in correct format.")
    db_name = fields.Char(string="Database Name", required=True,
                          help="Provide the database name.")
    db_username = fields.Char(string="Database Username", required=True,
                              help="Provide the Username.")
    db_password = fields.Char(string="Database Password", required=True,
                              help="Provide the db password.")
    csv_file_path = fields.Char(string="File Path", required=True,
                                help="Provide the file location path.")

    def action_fetch_data(self):
        """To fetch the data from the database"""
        common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        uid = common.authenticate(self.db_name, self.db_username,
                                  self.db_password, {})
        model = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        model_name = 'stock.move'
        field = ['product_id', 'date', 'product_uom_qty', 'id', 'reference',
                 'location_id', 'location_dest_id', 'origin']
        data = model.execute_kw(self.db_name, uid, self.db_password,
                                model_name, 'search_read',
                                [[]], {'fields': field})
        for item in data:
            item['product_id'] = item['product_id'][1] if item[
                'product_id'] else ''
            item['location_id'] = item['location_id'][1] if item[
                'location_id'] else ''
            item['location_dest_id'] = item['location_dest_id'][1] if item[
                'location_dest_id'] else ''
        for items in data:
            items['item_id'] = items.pop('product_id', '')
            items['timestamp'] = items.pop('date', '')
            items['demand'] = items.pop('product_uom_qty', '')

        new_headers = ['item_id', 'timestamp', 'demand', 'id', 'reference',
                       'location_id', 'location_dest_id', 'origin']
        with open(self.csv_file_path, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=new_headers)
            writer.writeheader()
            writer.writerows(data)
        return {
            'name': _('Push to Bucket'),
            'type': 'ir.actions.act_window',
            'res_model': 'amazon.bucket',
            'view_mode': 'form',
            'target': 'current'
        }

    def get_file_path(self):
        """To get the file path"""
        data = self.search([], limit=1)
        file_path = data.csv_file_path
        return file_path
