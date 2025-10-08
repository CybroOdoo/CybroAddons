# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    @api.model
    def search_params(self, start_date, end_date, enabled_companies):
        """Method to get domain for searching."""
        if start_date and end_date:
            search_params = [('expiration_date', '>=', start_date),
                             ('expiration_date', '<=', end_date),
                             ('company_id', 'in', enabled_companies)]
        elif start_date:
            search_params = [('expiration_date', '>=', start_date),
                             ('company_id', 'in', enabled_companies)]
        else:
            search_params = [('company_id', 'in', enabled_companies)]
        return search_params

    @api.model
    def get_product_expiry(self, *args):
        """Method to get products that expires in 1 day ,7 days,30 days
        and 120 days.
        Args:
            *args(dict):Start date and End date to add filtration
        Returns:
            dict: A dict contains 1 day ,7 day ,30 day,120 day, and their
             respective counts of products that will expire.
        """
        data = [{"one_day": [], "counts": 0},
                {"seven_day": [], "counts": 0},
                {"thirty_day": [], "counts": 0},
                {"one_twenty_day": [], "counts": 0}]
        search_params = self.search_params(args[0].get('start_date'),
                                           args[0].get('end_date'), args[1])
        for record in self.search(search_params):
            if record.expiration_date and record.product_qty != 0:
                date_difference = (fields.Date.to_date(
                    record.expiration_date) - fields.Date.today()).days
                if date_difference == 1:
                    data[0]["one_day"].append(record.id)
                    data[0]["counts"] += record.product_qty
                elif 7 >= date_difference >= 1:
                    data[1]["seven_day"].append(record.id)
                    data[1]["counts"] += record.product_qty
                elif 30 >= date_difference > 7:
                    data[2]["thirty_day"].append(record.id)
                    data[2]["counts"] += record.product_qty
                elif 120 >= date_difference > 30:
                    data[3]["one_twenty_day"].append(record.id)
        return data

    @api.model
    def get_product_expired_today(self, enabled_companies):
        """
        Method to get products that expired today
        Returns:
            int:count of products.
        """
        count = len([record for record in self.search([]) if
                    record.expiration_date and
                    fields.Date.to_date(record.expiration_date) == fields.date.today() and
                    record.company_id.id in enabled_companies])
        return count

    @api.model
    def get_expired_product(self, *args):
        """
        Method to get products that expired
        Args:
            *args(dict):Start date and End date to add filtration.
        Returns:
            dict: A dict that contains expired products and their count.
        """
        search_params = self.search_params(args[0].get('start_date'),
                                           args[0].get('end_date'))
        products_dict = {record: {'product_qty': record.product_qty,
                                  'product': record.product_id.name}
                         for record in self.search(search_params)
                         if record.expiration_date and record.product_qty != 0
                         and record.product_expiry_alert}
        expired_products_dict = {product: sum(data['product_qty']
                                              for lot, data in
                                              products_dict.items() if
                                              data['product'] == product)
                                 for product in set(
                data['product'] for lot, data in products_dict.items())}
        return expired_products_dict

    @api.model
    def get_product_expiry_by_category(self, *args):
        """
        Method to get category of products  that expired.
        Args:
            *args(dict):Start date and End date to add filtration.
        Returns:
            dict: A dict that contains expired products category and their
             count.
        """
        search_params = self.search_params(args[0].get('start_date'),
                                           args[0].get('end_date'))
        products_category_dict = {record: {'product_qty': record.product_qty,
                                           'product_category':
                                               record.product_id.categ_id.name}
                                  for record in self.search(search_params)
                                  if record.expiration_date and
                                  record.product_qty != 0
                                  and record.product_expiry_alert}
        expired_product_category_dict = {product: sum(data['product_qty']
                                                      for lot, data in
                                                      products_category_dict.
                                                      items() if
                                                      data['product_category']
                                                      == product)
                                         for product in
                                         set(data['product_category']
                                             for lot, data in
                                             products_category_dict.items())}
        return expired_product_category_dict

    @api.model
    def get_near_expiry_product(self, *args):
        """
        Method to get products that will expire in coming 7 days.
        Returns:
            dict:A dict that contains products and their count
        """
        search_params = self.search_params(args[0].get('start_date'),
                                           args[0].get('end_date'))
        if len(search_params) != 0:
            product_dict = {record: {'product_name': record.product_id.name,
                                     'product_qty': record.product_qty
                                     }
                            for record in self.search(search_params)
                            if
                            record.expiration_date and record.product_qty != 0}

        else:
            product_dict = {record: {'product_name': record.product_id.name,
                                     'product_qty': record.product_qty
                                     }
                            for record in self.search([])
                            if
                            record.expiration_date and record.product_qty and 7 >=
                            (fields.Date.to_date(record.expiration_date) -
                             fields.Date.today()).days > 0}
        nearby_exp_products_dict = {product: sum(
            data['product_qty'] for lot, data in product_dict.items() if
            data['product_name'] == product)
            for product in
            set(data['product_name'] for lot, data in
                product_dict.items())
        }
        return nearby_exp_products_dict

    @api.model
    def get_near_expiry_category(self, *args):
        """
        Method to get cate'gory of products  that will expire in coming 7 days.
        Returns:
            dict:A dict that contains category and their count
        """
        search_params = self.search_params(args[0].get('start_date'),
                                           args[0].get('end_date'))
        if len(search_params) != 0:
            product_dict = {
                record: {'category': record.product_id.categ_id.name,
                         'product_qty': record.product_qty
                         }
                for record in self.search(search_params)
                if
                record.expiration_date and record.product_qty != 0}
        else:
            product_dict = {record: {'category': record.product_id.categ_id.name,
                                     'product_qty': record.product_qty
                                     }
                            for record in self.search([])
                            if
                            record.expiration_date and record.product_qty and 7 >=
                            (fields.Date.to_date(record.expiration_date) -
                             fields.Date.today()).days > 0}

        nearby_exp_products_dict = {product: sum(
            data['product_qty'] for lot, data in product_dict.items() if
            data['category'] == product)
            for product in
            set(data['category'] for lot, data in
                product_dict.items())
        }
        return nearby_exp_products_dict

    @api.model
    def get_expire_product_location(self, *args):
        """Method to get products locations that will expire
         in coming 7 days
         Returns:
             dict:A dict of location and their respective count
         """
        search_params = self.search_params(args[0].get('start_date'),
                                           args[0].get('end_date'))
        if len(search_params) != 0:
            location_dict = {
                record: {'location': location.location_id.display_name,
                         'count': location.inventory_quantity_auto_apply} for
                record in self.search(search_params) if
                record.expiration_date and record.product_qty != 0
                for location in record.quant_ids if
                location.inventory_quantity_auto_apply > 0}
        else:
            location_dict = {
                record: {'location': location.location_id.display_name,
                         'count': location.inventory_quantity_auto_apply} for
                record in self.search([]) if
                record.expiration_date and record.product_qty and 7 >= (
                        fields.Date.to_date(record.expiration_date) - fields.Date.today()).days > 0
                for location in record.quant_ids if
                location.inventory_quantity_auto_apply > 0}
        nearby_expiry_location = {product: sum(
            data['count'] for lot, data in location_dict.items() if
            data['location'] == product) for product in set(
            data['location'] for lot, data in location_dict.items())}
        return nearby_expiry_location

    @api.model
    def get_expire_product_warehouse(self, *args):
        """Method to get products warehouse that will expire
                 in coming 7 days
            Returns:
                dict:A dict of warehouse and their respective counts.
        """
        search_params = self.search_params(args[0].get('start_date'),
                                           args[0].get('end_date'))
        if len(search_params) != 0:
            warehouse_dict = {
                record: {
                    'warehouse': location.location_id.warehouse_id.display_name,
                    'count': location.inventory_quantity_auto_apply} for
                record in self.search([]) if
                record.expiration_date and record.product_qty != 0
                for location in record.quant_ids if
                location.inventory_quantity_auto_apply > 0}
        else:
            warehouse_dict = {
                record: {
                    'warehouse': location.location_id.warehouse_id.display_name,
                    'count': location.inventory_quantity_auto_apply} for
                record in self.search([]) if
                record.expiration_date and record.product_qty and 7 >= (
                        fields.Date.to_date(
                            record.expiration_date) - fields.Date.today()).days > 0
                for location in record.quant_ids if
                location.inventory_quantity_auto_apply > 0}
        nearby_expiry_warehouse = {product: sum(
            data['count'] for lot, data in warehouse_dict.items() if
            data['warehouse'] == product) for product in set(
            data['warehouse'] for lot, data in warehouse_dict.items())}
        return nearby_expiry_warehouse

    @api.model
    def get_today_expire(self):
        """Method to get products that will expire current day
           Returns:
               A dict which includes list of products id,
               list of products name, list of products quantity, and
               list of products category.
        """
        data = {'id': [], 'name': [], 'qty': [], 'categ': []}
        for line in self.search([]):
            if line.expiration_date and line.expiration_date.date() == fields.date.today():
                data['id'].append(line.id)
                data['name'].append(line.product_id.name)
                data['qty'].append(line.product_qty)
                found_category = False
                for rec in data['categ']:
                    for key, value in rec.items():
                        if line.product_id.categ_id.name == key:
                            rec[key] += line.product_qty
                            found_category = True
                            break
                if not found_category:
                    data['categ'].append({line.product_id.categ_id.name: line.product_qty})
        return data
