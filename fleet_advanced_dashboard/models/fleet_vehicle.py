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
from odoo import api, models


class FleetVehicle(models.Model):
    """
    The FleetVehicle class provides the data to the js when the dashboard is
    loaded.
        Methods:
            get_tiles_data(self):
                when the page is loaded get the data from different models and
                transfer to the js file.
                return a dictionary variable.
            get_graph_data(self, month, flag, model_ids):
                month and flag are Integer variables and model_ids is object.
                In this methode getting data to the corresponding month from the
                model_ids and return
                it to the get_tiles_data methode. return a list variable.
    """
    _inherit = 'fleet.vehicle'

    @api.model
    def get_tiles_data(self, model_id):
        """
        Summary:
            when the page is loaded get the data from different models and
            transfer to the js file.
            return a dictionary variable.
        return:
            type:It is a dictionary variable. This dictionary contain data that
            affecting the dashboard view.
        """
        # Checking login user is manager or not.
        if self.env.user.has_group('fleet.fleet_group_manager'):
            flag = 1
            # Use the computed `odometer` field on each vehicle — it already
            # holds the latest reading, so we avoid summing all history.
            all_fleet_vehicles = self.env['fleet.vehicle'].search([('active', '=', True)])
            fleet_vehicle_odometer_ids = self.env[
                'fleet.vehicle.odometer'].search([('vehicle_id', '!=', False)])
            fleet_vehicle_log_services_ids = self.env[
                'fleet.vehicle.log.services'].search([('active', '=', True)])
            service_type_list = [['Service Type', 'Total Repair']]
            # Getting service type and it's total services.
            for fleet_service_type_id in self.env['fleet.service.type'].search(
                    [('category', '=', 'service')]):
                service_types_list = [fleet_service_type_id.name,
                                      self.env['fleet.vehicle.log.services']
                                      .search_count([('service_type_id', '=',
                                                      fleet_service_type_id.id)])]
                if service_types_list not in service_type_list:
                    service_type_list.append(service_types_list)
            fleet_vehicle_log_contract_ids = self.env[
                'fleet.vehicle.log.contract'].search([('active', '=', True)])
            filtered_fleet_vehicle_log_contract_ids = \
                fleet_vehicle_log_contract_ids.filtered(
                    lambda fleet_vehicle_log_contract_id:
                    fleet_vehicle_log_contract_id.state not in [
                        'expired',
                        'closed'])
            fleet_model_list = [fleet_vehicle_id.model_id.id for
                                fleet_vehicle_id in all_fleet_vehicles
                                if fleet_vehicle_id.model_id]
            fleet_model_list = [fleet_model for n, fleet_model in
                                enumerate(fleet_model_list) if
                                fleet_model not in fleet_model_list[:n]]
            fleet_manufacture_list = [fleet_vehicle_id.model_id.brand_id.id for
                                      fleet_vehicle_id in all_fleet_vehicles
                                      if fleet_vehicle_id.model_id and
                                      fleet_vehicle_id.model_id.brand_id]
            fleet_manufacture_list = [fleet_manufacture for n, fleet_manufacture
                                      in enumerate(fleet_manufacture_list) if
                                      fleet_manufacture not in
                                      fleet_manufacture_list[:n]]
            if model_id and model_id != 'null':
                all_vehicles = self.env['fleet.vehicle'].search_count([('model_id', '=', int(model_id))])
            else:
                all_vehicles = self.env['fleet.vehicle'].search_count([('active', '=', True)])

            return {
                # Sum the latest odometer value per vehicle (not all history)
                'total_odometer': sum(all_fleet_vehicles.mapped('odometer')),
                'service_cost': sum(
                    fleet_vehicle_log_services_ids.mapped('amount')),
                'recurring_cost': sum(
                    filtered_fleet_vehicle_log_contract_ids.mapped(
                        'cost_generated')),
                'all_vehicles': all_vehicles,
                'service_type': service_type_list,
                'service_cost_list': self.get_graph_data(6, 1, fleet_vehicle_log_services_ids),
                'odometer_value_list': self.get_graph_data(13, 0,
                                                           fleet_vehicle_odometer_ids),
                'fleet_state': [{'id': fleet_vehicle_state_id.id,
                                 'state': fleet_vehicle_state_id.name,
                                 'number': self.env[
                                     'fleet.vehicle'].search_count(
                                     [('state_id', '=',
                                       fleet_vehicle_state_id.id)])}
                                for fleet_vehicle_state_id in
                                self.env['fleet.vehicle.state'].search(
                                    [('name', '!=', False)])],
                'admin_odometer_list': [fleet_vehicle_odometer_id.id
                                        for fleet_vehicle_odometer_id in
                                        fleet_vehicle_odometer_ids],
                'admin_fleet_cost_list': [fleet_vehicle_log_services_id.id for
                                          fleet_vehicle_log_services_id in
                                          fleet_vehicle_log_services_ids],
                'admin_recurring_list': [fleet_vehicle_log_contract_id.id for
                                         fleet_vehicle_log_contract_id in
                                         fleet_vehicle_log_contract_ids if
                                         fleet_vehicle_log_contract_id.state not in [
                                             'expired',
                                             'closed']],
                'fleet_vehicle_list': all_fleet_vehicles.ids,
                'fleet_model_list': fleet_model_list,
                'fleet_manufacture_list': fleet_manufacture_list,
                'flag': flag,
            }
        else:
            flag = 0
            non_admin_vehicles = self.env['fleet.vehicle'].search(
                [('manager_id', '=', self.env.uid)])
            fleet_vehicle_odometer_ids = self.env[
                'fleet.vehicle.odometer'].search(
                [('vehicle_id.manager_id', '=', self.env.uid)])
            # Getting total service cost.
            fleet_vehicle_log_services_ids = self.env[
                'fleet.vehicle.log.services'].search(
                [('vehicle_id.manager_id', '=', self.env.uid)])
            service_type_list = [['Service Type', 'Total Repair']]
            # Getting service type and it's total services.
            for fleet_service_type_id in self.env['fleet.service.type'].search(
                    [('category', '=', 'service')]):
                service_types_list = [fleet_service_type_id.name,
                                      self.env['fleet.vehicle.log.services'].
                                      search_count(
                                          [('service_type_id', '=',
                                            fleet_service_type_id.id),
                                           ('vehicle_id.manager_id', '=',
                                            self.env.uid)])]
                if service_types_list not in service_type_list:
                    service_type_list.append(service_types_list)
            fleet_vehicle_log_contract_ids = self.env[
                'fleet.vehicle.log.contract'].search(
                [('vehicle_id.manager_id', '=', self.env.uid)])
            filtered_fleet_vehicle_log_contract_ids = \
                fleet_vehicle_log_contract_ids.filtered(
                    lambda fleet_vehicle_log_contract_id:
                    fleet_vehicle_log_contract_id.state not in [
                        'expired',
                        'closed'])
            # Getting vehicle status and total number vehicles for the
            # Corresponding state.
            model_list = [fleet_vehicle_id.model_id.id for fleet_vehicle_id in
                          non_admin_vehicles if fleet_vehicle_id.model_id]
            model_list = [model for n, model in enumerate(model_list) if
                          model not in model_list[:n]]
            manufacture_list = [fleet_vehicle_id.model_id.brand_id.id for
                                fleet_vehicle_id in non_admin_vehicles if
                                fleet_vehicle_id.model_id and fleet_vehicle_id.model_id.brand_id]
            manufacture_list = [manufacture for n, manufacture in
                                enumerate(manufacture_list) if
                                manufacture not in manufacture_list[:n]]
            vehicle_domain = [('manager_id', '=', self.env.uid)]
            if model_id and model_id != 'null':
                vehicle_domain.append(('model_id', '=', int(model_id)))
            all_vehicles = self.env['fleet.vehicle'].search_count(vehicle_domain)

            return {
                'total_odometer': sum(non_admin_vehicles.mapped('odometer')),
                'service_cost': sum(
                    fleet_vehicle_log_services_ids.mapped('amount')),
                'recurring_cost': sum(
                    filtered_fleet_vehicle_log_contract_ids.mapped(
                        'cost_generated')),
                'all_vehicles': all_vehicles,
                'service_type': service_type_list,
                'service_cost_list': self.get_graph_data(6, 1, fleet_vehicle_log_services_ids),
                'odometer_value_list': self.get_graph_data(13, 0,
                                                           fleet_vehicle_odometer_ids),
                'fleet_state': [{'id': fleet_vehicle_state_id.id,
                                 'state': fleet_vehicle_state_id.name,
                                 'number': self.env[
                                     'fleet.vehicle'].search_count(
                                     [('state_id', '=',
                                       fleet_vehicle_state_id.id),
                                      ('manager_id', '=',
                                       self.env.uid)])}
                                for fleet_vehicle_state_id in
                                self.env['fleet.vehicle.state'].search(
                                    [('name', '!=', False)])],
                'flag': flag,
                'model_list': model_list,
                'manufacture_list': manufacture_list
            }

    def get_graph_data(self, month, flag, model_ids):
        """
        summary:
            In this meth ode getting data to the corresponding month from the
            model_ids and return
            it to the get_tiles_data methode.
        Args:
            month(int): This parameter used to calculate the month range.
            flag(int): This parameter used to differentiate the need and
            performing different functions.
            model_ids(obj): This parameter used to identify the model to
            performs the function.
        Returns:
            type:list of lists , it contains the data for the corresponding
            month.
        """
        data_list = [['Month', '']]
        # Getting last "month" range
        for i in range(month):
            previous_month = date.today().replace(day=5) - timedelta(
                days=i * 30)
            first_day_of_previous_month = previous_month.replace(day=1)
            last_day_of_previous_month = previous_month.replace(
                day=1) + timedelta(days=32)
            last_day_of_previous_month = last_day_of_previous_month.replace(
                day=1) - timedelta(days=1)
            monthly_service_cost = 0
            if flag == 1:
                # Getting data to the corresponding month and append to
                # The data_list
                for fleet_vehicle_log_services_id in model_ids:
                    if first_day_of_previous_month < \
                            fleet_vehicle_log_services_id.date < \
                            last_day_of_previous_month:
                        monthly_service_cost += \
                            fleet_vehicle_log_services_id.amount
                data_list.append([
                    previous_month.strftime("%b"), monthly_service_cost
                ])
            else:
                # Getting data to the corresponding month and append to the
                # data_list
                monthly_odometer_value = 0
                for fleet_vehicle_odometer_id in model_ids:
                    if first_day_of_previous_month < fleet_vehicle_odometer_id.date < last_day_of_previous_month:
                        monthly_odometer_value += fleet_vehicle_odometer_id.value
                data_list.append(
                    [previous_month.strftime("%b-%y"), monthly_odometer_value])
        return data_list
