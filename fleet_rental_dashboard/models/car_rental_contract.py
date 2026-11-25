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
import base64
from odoo import api, models


def _binary_to_base64(binary_val):
    if not binary_val:
        return False
    if hasattr(binary_val, 'to_base64'):
        return binary_val.to_base64()
    if isinstance(binary_val, bytes):
        return base64.b64encode(binary_val).decode('utf-8')
    return str(binary_val)


def _get_date_domain(start_date=False, end_date=False):
    domain = []
    if start_date and end_date:
        domain.extend([
            ('rent_start_date', '<=', end_date),
            ('rent_end_date', '>=', start_date),
        ])
    elif start_date:
        domain.append(('rent_end_date', '>=', start_date))
    elif end_date:
        domain.append(('rent_start_date', '<=', end_date))
    return domain


class DashboardFleetRental(models.Model):
    """Class for new function to get vehicle and customers details
           vehicle_most_rented
                             function for getting most rented vehicle which
           cars_availability
                            function for getting available and running car's
           car_details
                        function for getting the car details
           top_customers
                        function  for getting top 10 customers
       """

    _inherit = "car.rental.contract"

    @api.model
    def vehicle_most_rented(self, start_date=False, end_date=False):
        """function for getting most rented vehicle if filters enabled or not
                args:
                    start_date:filter for start date
                    end_date:end date filter
                return:
                      result which include vehicle details and its count
        """
        domain = [('state', 'not in', ['draft', 'cancel'])] + _get_date_domain(start_date, end_date)

        groups = self.env['car.rental.contract']._read_group(
            domain=domain,
            groupby=['vehicle_id'],
            aggregates=['__count'],
            order='__count DESC',
        )
        cars = []
        count = []
        for vehicle, num in groups:
            if vehicle and num > 0:
                cars.append(vehicle.display_name or vehicle.name)
                count.append(num)
        return {
            'name': cars,
            'num': count,
        }

    @api.model
    def cars_availability(self, start_date=False, end_date=False):
        """function for getting available and running cars count
            return:
                  count of available and running cars in result"""
        available_cars = self.env['fleet.vehicle'].search_count(
            [('rental_check_availability', '=', True)])
        domain = [('state', '=', 'running')] + _get_date_domain(start_date, end_date)
        cars_running = self.env['car.rental.contract'].search_count(domain)
        result = {
            'available_cars': available_cars,
            'cars_running': cars_running
        }
        return result

    @api.model
    def car_details(self, start_date=False, end_date=False):
        """
        function for getting details of running and available cars
            return:
                    values which include details of running and available cars
        """
        domain = [('state', 'in', ['running', 'reserved'])] + _get_date_domain(start_date, end_date)
        running_cars = self.env['car.rental.contract'].search(domain)
        cars_available = self.env['fleet.vehicle'].search(
            [('rental_check_availability', '=', True)])
        running_details = []
        available_cars = []
        for record in running_cars:
            running_details.append({
                'vehicle': record.vehicle_id.display_name or record.vehicle_id.name or '',
                'start_date': str(record.rent_start_date) if record.rent_start_date else '',
                'end_date': str(record.rent_end_date) if record.rent_end_date else '',
                'customer': record.customer_id.name or '',
                'phone': record.customer_id.phone or '',
            })
        for record in cars_available:
            available_cars.append({
                'available_car': record.display_name or record.name or '',
            })
        values = {
            'running_details': running_details,
            'available_cars': available_cars
        }
        return values

    @api.model
    def top_customers(self, start_date=False, end_date=False):
        """function for getting top 10 customers
            return top customers which include their name,image and email
        """
        domain = [('state', 'not in', ['draft', 'cancel'])] + _get_date_domain(start_date, end_date)
        groups = self.env['car.rental.contract']._read_group(
            domain=domain,
            groupby=['customer_id'],
            aggregates=['__count'],
            order='__count DESC',
            limit=10,
        )
        top_customers = []
        for partner, count in groups:
            if partner:
                image = partner.avatar_128 or partner.image_1920
                top_customers.append({
                    'id': partner.id,
                    'name': partner.name,
                    'image': _binary_to_base64(image),
                    'email': partner.email or '',
                })
        return top_customers
