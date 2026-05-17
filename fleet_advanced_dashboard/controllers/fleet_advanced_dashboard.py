# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Prasudhi A (odoo@cybrosys.com)
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
################################################################################
from datetime import date, timedelta
from odoo import http
from odoo.http import request


class FleetFilter(http.Controller):
    """
        The FleetFilter class provides the filter option to the js.
        When applying the filter return the corresponding data.
            Methods:
                fleet_filter(self):
                    when the page is loaded adding filter options to the selection
                    field.
                    return a list variable.
                fleet_filter_data(self,**kw):
                    after applying the filter receiving the values and return the
                    filtered data.
        """

    @http.route('/fleet/filter', auth='public', type='jsonrpc')
    def fleet_filter(self):
        """
        Summary:
            transferring data to the selection field that works as a filter
        Returns:
            type:list of lists , it contains the data for the corresponding
            filter.
        """
        fleet_vehicle_ids = request.env['fleet.vehicle'].search([])
        driver_list = request.env['res.partner'].search_read([], ['name'])
        vehicle_list = [{'id': fleet_vehicle_id.model_id.id,
                         'name': fleet_vehicle_id.model_id.name}
                        for fleet_vehicle_id in fleet_vehicle_ids]
        vehicle_list = [vehicle for n, vehicle in
                        enumerate(vehicle_list) if
                        vehicle not in vehicle_list[:n]]
        manufacturers_list = [{'id': fleet_vehicle_id.model_id.brand_id.id,
                               'name': fleet_vehicle_id.model_id.brand_id.name}
                              for fleet_vehicle_id in fleet_vehicle_ids]
        manufacturers_list = [manufacturer for n, manufacturer in
                              enumerate(manufacturers_list) if
                              manufacturer not in manufacturers_list[:n]]
        return {'drivers': driver_list, 'vehicles': vehicle_list, 'manufactures': manufacturers_list}

    @http.route('/fleet_advanced_dashboard/filter_data', auth='public',
                type='jsonrpc')
    def fleet_filter_data(self, **kw):
        """Function used to filter data in fleet dashboard"""
        data = kw.get('data')
        driver = [partner.id for partner in
                  request.env['res.partner'].search([])] \
            if data['driver'] == 'null' else [int(data['driver'])]

        vehicle = [fleet_vehicle_id.id for fleet_vehicle_id in
                   request.env['fleet.vehicle.model'].search([])] \
            if data['vehicle'] == 'null' else [int(data['vehicle'])]

        vehicle_domain = [("model_id", "in", vehicle)]

        if data['manufacturer'] != "null":
            vehicle_domain.append(("model_id.brand_id", "=", int(data['manufacturer'])))

        if data['driver'] != "null":
            vehicle_domain.append(("driver_id", "=", int(data['driver'])))

        fleet_vehicle_list = request.env['fleet.vehicle'].search(vehicle_domain)

        manufacturer = [fleet_vehicle_id.model_id.brand_id.id for
                        fleet_vehicle_id in fleet_vehicle_list] \
            if data['manufacturer'] == 'null' else [int(data['manufacturer'])]

        if data['date'] == 'null':
            fleet_vehicle_odometer_ids = request.env[
                'fleet.vehicle.odometer'].search(
                [("vehicle_id", 'in', fleet_vehicle_list.ids),
                 ("vehicle_id.brand_id", "in", manufacturer),
                 ("driver_id", "in", driver)])
            fleet_vehicle_log_contract_ids = request.env[
                'fleet.vehicle.log.contract'].search(
                [("vehicle_id.model_id", 'in', vehicle),
                 ("vehicle_id.model_id.brand_id", 'in', manufacturer),
                 ("state", "not in", ['expired', 'closed']),
                 ("purchaser_id", "in", driver)])
            fleet_vehicle_log_services_ids = request.env[
                'fleet.vehicle.log.services'].search(
                [("vehicle_id.model_id", 'in', vehicle),
                 ("vehicle_id.model_id.brand_id", 'in', manufacturer),
                 ("purchaser_id", "in", driver)])
        else:
            range_date = date.today() - timedelta(days=int(data['date']))
            fleet_vehicle_odometer_ids = request.env[
                'fleet.vehicle.odometer'].search(
                [("vehicle_id", 'in', fleet_vehicle_list.ids),
                 ("vehicle_id.brand_id", "in", manufacturer),
                 ("driver_id", "in", driver),
                 ("date", ">", range_date)])
            fleet_vehicle_log_contract_ids = request.env[
                'fleet.vehicle.log.contract'].search(
                [("vehicle_id.model_id", 'in', vehicle),
                 ("vehicle_id.model_id.brand_id", 'in', manufacturer),
                 ("state", "not in", ['expired', 'closed']),
                 ("purchaser_id", "in", driver),
                 ("expiration_date", ">", range_date)])
            fleet_vehicle_log_services_ids = request.env[
                'fleet.vehicle.log.services'].search(
                [("vehicle_id.model_id", 'in', vehicle),
                 ("vehicle_id.model_id.brand_id", 'in', manufacturer),
                 ("purchaser_id", "in", driver),
                 ("date", ">", range_date)])

        total_odometer = sum(fleet_vehicle_odometer_ids.mapped('value'))
        admin_odometer_list = fleet_vehicle_odometer_ids.ids

        service_cost = sum(fleet_vehicle_log_services_ids.mapped('amount'))
        admin_fleet_cost_list = fleet_vehicle_log_services_ids.ids

        recurring_cost = sum(
            fleet_vehicle_log_contract_ids.mapped('cost_generated'))
        admin_recurring_list = fleet_vehicle_log_contract_ids.ids

        odometer_monthly = request.env['fleet.vehicle'].get_graph_data(
            13, 0, fleet_vehicle_odometer_ids
        )

        service_cost_monthly = request.env['fleet.vehicle'].get_graph_data(
            6, 1, fleet_vehicle_log_services_ids
        )

        service_type = [['Service Type', 'Total Repair']]
        for st in request.env['fleet.service.type'].search([]):
            count = request.env['fleet.vehicle.log.services'].search_count([
                ('service_type_id', '=', st.id),
                ('vehicle_id.model_id', 'in', vehicle),
                ('vehicle_id.model_id.brand_id', 'in', manufacturer),
                ('purchaser_id', 'in', driver),
            ])
            service_type.append([st.name, count])

        filtered_models = list(
            set(fleet_vehicle_list.mapped("model_id").ids)
        )

        filtered_manufacturers = list(
            set(fleet_vehicle_list.mapped("model_id.brand_id").ids)
        )

        return {
            'total_odometer': total_odometer,
            'service_cost': service_cost,
            'recurring_cost': recurring_cost,

            'admin_odometer_list': admin_odometer_list,
            'admin_fleet_cost_list': admin_fleet_cost_list,
            'admin_recurring_list': admin_recurring_list,

            'fleet_vehicle_list': fleet_vehicle_list.ids,

            'fleet_model_list': filtered_models,
            'fleet_manufacture_list': filtered_manufacturers,

            'total_vehicles': len(fleet_vehicle_list.ids),

            'odometer_value_list': odometer_monthly,
            'service_cost_list': service_cost_monthly,
            'service_type': service_type,
        }
