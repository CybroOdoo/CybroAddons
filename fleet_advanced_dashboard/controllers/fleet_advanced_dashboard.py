# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

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

    @http.route('/fleet/filter', auth='user', type='json')
    def fleet_filter(self):
        """
        Summary:
            transferring data to the selection field that works as a filter
        Returns:
            type:list of lists , it contains the data for the corresponding
            filter.
        """
        is_manager = request.env.user.has_group('fleet.fleet_group_manager')
        domain = [] if is_manager else [('manager_id', '=', request.env.uid)]
        fleet_vehicle_ids = request.env['fleet.vehicle'].search(domain)
        # Only list partners who are drivers of accessible vehicles
        driver_partners = fleet_vehicle_ids.mapped('driver_id')
        driver_list = [{'id': driver.id, 'name': driver.name}
                       for driver in driver_partners if driver]
        # Getting vehicles model data
        vehicle_list = [{'id': fleet_vehicle_id.model_id.id,
                         'name': fleet_vehicle_id.model_id.name}
                        for fleet_vehicle_id in fleet_vehicle_ids
                        if fleet_vehicle_id.model_id]
        vehicle_list = [vehicle for n, vehicle in
                        enumerate(vehicle_list) if
                        vehicle not in vehicle_list[:n]]
        # Getting vehicles brand data
        manufacturers_list = [{'id': fleet_vehicle_id.model_id.brand_id.id,
                               'name': fleet_vehicle_id.model_id.brand_id.name}
                              for fleet_vehicle_id in fleet_vehicle_ids
                              if fleet_vehicle_id.model_id and
                              fleet_vehicle_id.model_id.brand_id]
        manufacturers_list = [manufacturer for n, manufacturer in
                              enumerate(manufacturers_list) if
                              manufacturer not in manufacturers_list[:n]]
        return {'drivers': driver_list, 'vehicles': vehicle_list, 'manufactures': manufacturers_list}

    @http.route('/fleet_advanced_dashboard/filter_data', auth='user',
                type='json')
    def fleet_filter_data(self, **kw):
        data = kw.get('data')

        v_domain = []
        if not request.env.user.has_group('fleet.fleet_group_manager'):
            v_domain.append(('manager_id', '=', request.env.uid))
        if data['driver'] != 'null':
            v_domain.append(('driver_id', '=', int(data['driver'])))
        if data['vehicle'] != 'null':
            v_domain.append(('model_id', '=', int(data['vehicle'])))
        if data['manufacturer'] != 'null':
            v_domain.append(('model_id.brand_id', '=', int(data['manufacturer'])))

        fleet_vehicle_list = request.env['fleet.vehicle'].search(v_domain)

        vehicle = request.env['fleet.vehicle.model'].search([('name', '!=', False)]).ids \
            if data['vehicle'] == 'null' else [int(data['vehicle'])]

        manufacturer = fleet_vehicle_list.mapped('model_id.brand_id').ids \
            if data['manufacturer'] == 'null' else [int(data['manufacturer'])]

        odo_domain = [("vehicle_id", 'in', fleet_vehicle_list.ids)]
        contract_domain = [("vehicle_id", 'in', fleet_vehicle_list.ids),
                           ("state", "not in", ['expired', 'closed'])]
        services_domain = [("vehicle_id", 'in', fleet_vehicle_list.ids)]

        if data['driver'] != 'null':
            driver_id = int(data['driver'])
            odo_domain.append(("driver_id", "=", driver_id))
            contract_domain.append(("purchaser_id", "=", driver_id))
            services_domain.append(("purchaser_id", "=", driver_id))

        if data['date'] != 'null':
            range_date = date.today() - timedelta(days=int(data['date']))
            odo_domain.append(("date", ">", range_date))
            contract_domain.append(("expiration_date", ">", range_date))
            services_domain.append(("date", ">", range_date))

        fleet_vehicle_odometer_ids = request.env[
            'fleet.vehicle.odometer'].search(odo_domain)
        fleet_vehicle_log_contract_ids = request.env[
            'fleet.vehicle.log.contract'].search(contract_domain)
        fleet_vehicle_log_services_ids = request.env[
            'fleet.vehicle.log.services'].search(services_domain)

        # Sum only the latest odometer reading per vehicle (not all history)
        latest_odo_per_vehicle = {}
        for odo in fleet_vehicle_odometer_ids.sorted('date'):
            latest_odo_per_vehicle[odo.vehicle_id.id] = odo.value
        total_odometer = sum(latest_odo_per_vehicle.values())
        admin_odometer_list = fleet_vehicle_odometer_ids.ids

        service_cost = sum(fleet_vehicle_log_services_ids.mapped('amount'))
        admin_fleet_cost_list = fleet_vehicle_log_services_ids.ids

        recurring_cost = sum(
            fleet_vehicle_log_contract_ids.mapped('cost_generated'))
        admin_recurring_list = fleet_vehicle_log_contract_ids.ids

        service_cost_list = request.env['fleet.vehicle'].get_graph_data(6, 1, fleet_vehicle_log_services_ids)
        odometer_value_list = request.env['fleet.vehicle'].get_graph_data(13, 0, fleet_vehicle_odometer_ids)

        service_type_list = [['Service Type', 'Total Repair']]
        for fleet_service_type_id in request.env['fleet.service.type'].search(
                [('category', '=', 'service')]):
            current_st_id = fleet_service_type_id.id
            repair_count = len(fleet_vehicle_log_services_ids.filtered(
                lambda l, st_id=current_st_id: l.service_type_id.id == st_id
            ))
            service_types_list = [fleet_service_type_id.name, repair_count]
            if service_types_list not in service_type_list:
                service_type_list.append(service_types_list)

        return [total_odometer, service_cost, recurring_cost,
                admin_odometer_list, admin_fleet_cost_list,
                admin_recurring_list, fleet_vehicle_list.ids, vehicle,
                manufacturer, len(fleet_vehicle_list.ids),
                service_cost_list, odometer_value_list, service_type_list]
