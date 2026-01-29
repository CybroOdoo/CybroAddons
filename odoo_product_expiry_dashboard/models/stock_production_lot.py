# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class StockProductionLot(models.Model):
    """Inherited to include the functions for fetching the data which is to be
     displayed on the dashboard"""
    _inherit = "stock.production.lot"

    @api.model
    def get_product_expiry(self, *args):
        """Returns the data to be displayed on the dashboard tiles"""
        expiry_dict = {"expired": 0, "today": 0, "one_day": 0, "seven_day": 0,
                       "thirty_day": 0,
                       "one_twenty_day": 0}
        search_params = []
        if args[0].get('start_date') and args[0].get('end_date'):
            search_params = [
                ('expiration_date', '>=', args[0].get('start_date')),
                ('expiration_date', '<=', args[0].get('end_date'))]
        elif args[0].get('start_date'):
            search_params = [
                ('expiration_date', '>=', args[0].get('start_date'))]
        elif args[0].get('end_date'):
            search_params = [('expiration_date', '<=', args[0].get('end_date'))]
        for record in self.search(search_params):
            if record.expiration_date and record.product_qty != 0:
                date_difference = (fields.Date.to_date(
                    record.expiration_date) - fields.Date.today()).days
                if date_difference == 0:
                    expiry_dict["today"] += record.product_qty
                elif date_difference == 1:
                    expiry_dict["one_day"] += record.product_qty
                elif 7 >= date_difference > 1:
                    expiry_dict["seven_day"] += record.product_qty
                elif 30 >= date_difference > 7:
                    expiry_dict["thirty_day"] += record.product_qty
                elif 120 >= date_difference > 30:
                    expiry_dict["one_twenty_day"] += record.product_qty
        search_params.append(('expiration_date', '<', fields.date.today()))
        expiry_dict["expired"] = \
            sum(self.search(search_params).mapped('product_qty'))
        return expiry_dict

    @api.model
    def get_expired_product(self, *args):
        """Function for fetching the expired products"""
        search_params = [('expiration_date', '<', fields.date.today())]
        if args[0].get('start_date'):
            search_params.append(
                ('expiration_date', '>=', args[0].get('start_date')))
        if args[0].get('end_date'):
            search_params.append(('expiration_date', '<=',
                                  args[0].get('end_date')))
        products_dict = {record: {'product_qty': record.product_qty,
                                  'product': record.product_id.name}
                         for record in self.search(search_params)}
        expired_products_dict = {product: sum(data['product_qty']
                                              for lot, data in
                                              products_dict.items() if
                                              data['product'] == product)
                                 for product in set(
                data['product'] for lot, data in products_dict.items())}
        return expired_products_dict

    @api.model
    def get_product_expiry_by_category(self, *args):
        """Functions for fetching the category of expired products"""
        search_params = [('expiration_date', '<', fields.date.today())]
        if args[0].get('start_date'):
            search_params.append(
                ('expiration_date', '>=', args[0].get('start_date')))
        if args[0].get('end_date'):
            search_params.append(('expiration_date', '<=',
                                  args[0].get('end_date')))
        products_category_dict = {record: {'product_qty': record.product_qty,
                                           'product_category':
                                               record.product_id.categ_id.name}
                                  for record in self.search(search_params)}
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
    def get_near_expiry_category(self):
        """Function for fetching the category of products expiring in 7 days"""
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
    def get_near_expiry_product(self):
        """Function for fetching the products expiring in 7 days"""
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
    def get_product_expired_today(self):
        """Function for fetching the products expiring today"""
        return len([record for record in self.search([]) if
                    record.expiration_date and
                    fields.Date.to_date(record.expiration_date) ==
                    fields.date.today()])

    @api.model
    def get_expire_product_location(self):
        """Function for fetching the location of products expiring in 7 days"""
        location_dict = {
            record: {'location': location.location_id.display_name,
                     'count': location.inventory_quantity_auto_apply} for
            record in self.search([]) if
            record.expiration_date and record.product_qty and 7 >= (
                    fields.Date.to_date(
                        record.expiration_date) - fields.Date.today()).days > 0
            for location in record.quant_ids if
            location.inventory_quantity_auto_apply > 0}
        nearby_expiry_location = {product: sum(
            data['count'] for lot, data in location_dict.items() if
            data['location'] == product) for product in set(
            data['location'] for lot, data in location_dict.items())}
        return nearby_expiry_location

    @api.model
    def get_expire_product_warehouse(self):
        """Function for fetching the warehouse of products expiring in 7 days"""
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
