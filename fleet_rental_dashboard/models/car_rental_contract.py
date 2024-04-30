# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
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
###############################################################################
from odoo import api, models


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
    def vehicle_most_rented(self, start_date, end_date):
        """function for getting most rented vehicle if filters enabled or not
                args:
                    start_date:filter for start date
                    end_date:end date filter
                return:
                      result which include vehicle details and its count
        """
        query = """SELECT vehicle_id,COUNT(*) AS num FROM car_rental_contract 
        WHERE state='done'"""
        if start_date:
            query += """ AND rent_start_date >= '%s'""" % start_date
        if end_date:
            query += """AND rent_start_date <= '%s'""" % end_date
        query += """GROUP BY vehicle_id ORDER BY num DESC"""
        self.env.cr.execute(query)
        results = self.env.cr.fetchall()
        cars = []
        count = []
        for vehicle_id, num in results:
            if num > 0:
                car = self.env['fleet.vehicle'].browse(vehicle_id)
                cars.append(
                    car.name
                )
                count.append(num)
        result = {
            'name': cars,
            'num': count
        }
        return result

    @api.model
    def cars_availability(self):
        """function for getting available and running cars count
            return:
                  count of available and running cars in result"""
        available_cars = self.env['fleet.vehicle'].search_count(
            [('rental_check_availability', '=', True)])
        cars_running = self.env['car.rental.contract'].search_count(
            [('state', '=', 'running')])
        result = {
            'available_cars': available_cars,
            'cars_running': cars_running
        }
        return result

    @api.model
    def car_details(self):
        """
        function for getting details of running and available cars
            return:
                    values which include details of running and available cars
        """
        running_cars = self.env['car.rental.contract'].search(
            [('state', '=', 'running')])
        cars_available = self.env['fleet.vehicle'].search(
            [('rental_check_availability', '=', True)])
        running_details = []
        available_cars = []
        for record in running_cars:
            running_details.append({'vehicle': record.vehicle_id.name,
                                    'start_date': record.rent_start_date,
                                    'end_date': record.rent_end_date,
                                    'customer': record.customer_id.name,
                                    'phone': record.customer_id.phone,
                                    })
        for record in cars_available:
            available_cars.append({
                'available_car': record.name,
            })
        values = {
            'running_details': running_details,
            'available_cars': available_cars
        }
        return values

    @api.model
    def top_customers(self):
        """function for getting top 10 customers
            return top customers which include their name,image and email
            """
        rental_partners_count = self.env['car.rental.contract'].read_group(
            [('state', 'in', ['done'])],
            fields=['customer_id'],
            groupby=['customer_id'], )
        sorted_rental_partners_count = sorted(rental_partners_count,
                                              key=lambda k: k[
                                                  'customer_id_count'],
                                              reverse=True)
        limited = sorted_rental_partners_count[:10]
        top_customers = []
        for rec in limited:
            partner = self.env['res.partner'].browse(rec['customer_id'][0])
            top_customers.append({
                'id': partner.id,
                'name': partner.name,
                'image': partner.image_1920,
                'email': partner.email
            })
        return top_customers
