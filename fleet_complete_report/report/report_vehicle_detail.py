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


class ReportVehicleDetail(models.AbstractModel):
    _name = 'report.fleet_complete_report.report_vehicle_detail'
    _description = 'Vehicle Details Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Overrides the method to create custom report with custom values
        :param docids: the recordset/ record from which the report action is
        invoked
        :param data: report data
        :return: data and recodsets to be used in the report template
        """
        if data is None:
            data = {}
        docs = self.env['vehicle.detail'].browse(
            self.env.context.get('active_id') or docids)
        lang = self.env['res.lang'].search(
            [('code', '=', self.env.context.get('lang'))], limit=1)
        if not lang:
            lang = self.env['res.lang'].search(
                [('code', '=', self.env.user.lang)], limit=1) or self.env['res.lang'].search([], limit=1)
        vehicle_ids = data.get('vehicle_ids')
        if vehicle_ids:
            vehicles = self.env['fleet.vehicle'].browse(vehicle_ids)
        else:
            vehicles = docs.vehicle_ids
        vehicles = vehicles.sorted(key=lambda rec: rec.state_id.sequence if rec.state_id else 0)
        states = docs.state_ids.sorted(key=lambda rec: rec.sequence)
        period = None
        end_date = docs.end_date
        if not end_date:
            end_date = fields.Date.context_today(self)
        if docs.start_date:
            date_format = lang.date_format if lang else '%Y-%m-%d'
            period = "From " + docs.start_date.strftime(
                date_format) + " To " + end_date.strftime(date_format)
        contracts = self.env['fleet.vehicle.log.contract'].sudo().search(
            [('vehicle_id', 'in', vehicles.ids),
             ('start_date', '<=', end_date),
             '|', ('expiration_date', '>=', docs.start_date),
             ('expiration_date', '=', False),
             ],
            order='vehicle_id ASC, state ASC, start_date DESC')
        services = self.env['fleet.vehicle.log.services'].sudo().search(
            [('vehicle_id', 'in', vehicles.ids),
             ('date_from', '>=', docs.start_date), ('date_from', '<=', end_date)],
            order='vehicle_id ASC, date_from DESC')
        odometers = self.env['fleet.vehicle.odometer'].sudo().search(
            [('vehicle_id', 'in', vehicles.ids),
             ('date', '>=', docs.start_date), ('date', '<=', end_date)],
            order='vehicle_id ASC, date DESC')
        drivers_history = self.env[
            'fleet.vehicle.assignation.log'].sudo().search(
            [('vehicle_id', 'in', vehicles.ids), ('date_start', '<=', end_date),
             '|', ('date_end', '>=', docs.start_date),
             ('date_end', '=', False)], order='vehicle_id ASC, date_start ASC')
        return {
            'doc_ids': self.ids,
            'docs': docs,
            'states': states,
            'state_names': ",  ".join(states.mapped('name')),
            'vehicles': vehicles,
            'vehicle_names': ",  ".join(vehicles.mapped('name')),
            'period': period,
            'contracts': contracts,
            'services': services,
            'odometers': odometers,
            'drivers_history': drivers_history,
        }
