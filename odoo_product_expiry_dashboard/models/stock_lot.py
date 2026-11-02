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
from odoo import api, fields, models


class StockLot(models.Model):
    """Inherited to include the functions for fetching the data which is to be
     displayed on the dashboard"""
    _inherit = "stock.lot"

    @api.model
    def get_product_expiry(self, *args):
        """Returns expiry info for dashboard tiles using overlapping ranges:
           - today           = 0 days
           - one_day         = 1 day
           - seven_day       = 1–7 days
           - thirty_day      = 1–30 days
           - one_twenty_day  = 1–120 days
           NOTE: product_qty must be non-zero
        """

        expiry_dict = {
            "expired": 0,
            "today": 0,
            "one_day": 0,
            "seven_day": 0,
            "thirty_day": 0,
            "one_twenty_day": 0,
        }

        today = fields.Date.today()

        # -------------------------------
        # Apply optional date filters
        # -------------------------------
        search_params = [('expiration_date', '!=', False)]

        params = args[0] if args and isinstance(args[0], dict) else {}

        if params.get('start_date'):
            search_params.append(
                ('expiration_date', '>=', params.get('start_date')))
        if params.get('end_date'):
            search_params.append(
                ('expiration_date', '<=', self._format_end_date_filter(params.get('end_date'))))

        # -------------------------------
        # Process lots
        # -------------------------------
        for record in self.search(search_params):
            if not record.expiration_date or record.product_qty <= 0:
                continue

            diff = (fields.Date.to_date(record.expiration_date) - today).days

            # expired
            if diff < 0:
                expiry_dict["expired"] += record.product_qty

            # today
            elif diff == 0:
                expiry_dict["today"] += record.product_qty

            # tomorrow
            elif diff == 1:
                expiry_dict["one_day"] += record.product_qty

            # 1–7 days
            if 1 <= diff <= 7:
                expiry_dict["seven_day"] += record.product_qty

            # 1–30 days
            if 1 <= diff <= 30:
                expiry_dict["thirty_day"] += record.product_qty

            # 1–120 days
            if 1 <= diff <= 120:
                expiry_dict["one_twenty_day"] += record.product_qty

        return expiry_dict

    @api.model
    def _format_end_date_filter(self, end_date):
        """Append end-of-day time 23:59:59 if end_date is a date string,
        ensuring lots expiring mid-day on the end date are included."""
        if not end_date:
            return end_date
        end_str = str(end_date).strip()
        if len(end_str) == 10:
            return f"{end_str} 23:59:59"
        return end_date

    @api.model
    def _format_totals_by_display_name(self, record_totals):
        """Format a dictionary of {record: qty} into {display_name: qty},
        disambiguating records with identical display names using their ID."""
        name_counts = {}
        for record in record_totals:
            name_counts[record.display_name] = name_counts.get(record.display_name, 0) + 1

        formatted = {}
        for record, qty in record_totals.items():
            if name_counts[record.display_name] > 1:
                label = f"{record.display_name} (#{record.id})"
            else:
                label = record.display_name
            formatted[label] = qty
        return formatted

    @api.model
    def get_expired_product(self, *args):
        """Function for fetching the expired products"""
        search_params = [('expiration_date', '<', fields.Date.today())]
        params = args[0] if args and isinstance(args[0], dict) else {}
        if params.get('start_date'):
            search_params.append(
                ('expiration_date', '>=', params.get('start_date')))
        if params.get('end_date'):
            search_params.append(
                ('expiration_date', '<=', self._format_end_date_filter(params.get('end_date'))))

        product_totals = {}
        for record in self.search(search_params):
            if not record.expiration_date or record.product_qty <= 0:
                continue
            product = record.product_id
            if product:
                product_totals[product] = product_totals.get(product, 0.0) + record.product_qty

        return self._format_totals_by_display_name(product_totals)

    @api.model
    def get_product_expiry_by_category(self, *args):
        """Functions for fetching the category of expired products"""
        search_params = [('expiration_date', '<', fields.Date.today())]
        params = args[0] if args and isinstance(args[0], dict) else {}
        if params.get('start_date'):
            search_params.append(
                ('expiration_date', '>=', params.get('start_date')))
        if params.get('end_date'):
            search_params.append(
                ('expiration_date', '<=', self._format_end_date_filter(params.get('end_date'))))

        category_totals = {}
        for record in self.search(search_params):
            if not record.expiration_date or record.product_qty <= 0:
                continue
            category = record.product_id.categ_id
            if category:
                category_totals[category] = category_totals.get(category, 0.0) + record.product_qty

        return self._format_totals_by_display_name(category_totals)

    @api.model
    def get_near_expiry_category(self):
        """Function for fetching the category of products expiring in 7 days"""
        today = fields.Date.today()
        category_totals = {}
        for record in self.search([('expiration_date', '!=', False)]):
            if not record.expiration_date or record.product_qty <= 0:
                continue
            diff = (fields.Date.to_date(record.expiration_date) - today).days
            if 1 <= diff <= 7:
                category = record.product_id.categ_id
                if category:
                    category_totals[category] = category_totals.get(category, 0.0) + record.product_qty

        return self._format_totals_by_display_name(category_totals)

    @api.model
    def get_near_expiry_product(self):
        """Function for fetching the products expiring in 7 days"""
        today = fields.Date.today()
        product_totals = {}
        for record in self.search([('expiration_date', '!=', False)]):
            if not record.expiration_date or record.product_qty <= 0:
                continue
            diff = (fields.Date.to_date(record.expiration_date) - today).days
            if 1 <= diff <= 7:
                product = record.product_id
                if product:
                    product_totals[product] = product_totals.get(product, 0.0) + record.product_qty

        return self._format_totals_by_display_name(product_totals)

    @api.model
    def get_product_expired_today(self):
        """Function for fetching the count of products expiring today"""
        today = fields.Date.today()
        expired_today_count = 0
        for record in self.search([('expiration_date', '!=', False)]):
            if record.expiration_date and fields.Date.to_date(record.expiration_date) == today:
                expired_today_count += 1
        return expired_today_count

    @api.model
    def get_expire_product_location(self):
        """Function for fetching the location of products expiring in 7 days"""
        today = fields.Date.today()
        location_totals = {}
        for record in self.search([('expiration_date', '!=', False)]):
            if not record.expiration_date or record.product_qty <= 0:
                continue
            diff = (fields.Date.to_date(record.expiration_date) - today).days
            if 1 <= diff <= 7:
                for quant in record.quant_ids:
                    if quant.quantity > 0 and quant.location_id.usage == 'internal':
                        loc_name = quant.location_id.display_name
                        location_totals[loc_name] = location_totals.get(loc_name, 0.0) + quant.quantity
        return location_totals

    @api.model
    def get_expire_product_warehouse(self):
        """Function for fetching the warehouse of products expiring in 7 days"""
        today = fields.Date.today()
        warehouse_totals = {}
        for record in self.search([('expiration_date', '!=', False)]):
            if not record.expiration_date or record.product_qty <= 0:
                continue
            diff = (fields.Date.to_date(record.expiration_date) - today).days
            if 1 <= diff <= 7:
                for quant in record.quant_ids:
                    if quant.quantity > 0 and quant.location_id.usage == 'internal':
                        wh = quant.location_id.warehouse_id
                        wh_name = wh.display_name if wh else quant.location_id.display_name
                        warehouse_totals[wh_name] = warehouse_totals.get(wh_name, 0.0) + quant.quantity
        return warehouse_totals
