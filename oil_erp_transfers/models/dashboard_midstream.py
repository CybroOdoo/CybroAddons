# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, models


class OilDashboardMidstream(models.TransientModel):
    """Extends the midstream dashboard with oil and gas transfer and fleet metrics."""

    _inherit = 'oil.dashboard.midstream'

    @api.model
    def get_dashboard_data(self):
        """Compile transfer statistics, fleet availability, and delivery performance data for the midstream dashboard."""
        res = super().get_dashboard_data()

        vehicles = self.env['fleet.vehicle'].search([('is_oil_gas_fleet', '=', True)])
        transfers = self.env['stock.picking'].search([
            ('is_oil_gas_transfer', '=', True),
            ('picking_type_code', '=', 'internal'),
        ])

        active_transfers = transfers.filtered(lambda picking: picking.state not in ('done', 'cancel'))
        done_transfers = transfers.filtered(lambda picking: picking.state == 'done')
        short_deliveries = done_transfers.filtered(lambda picking: picking.delivery_status == 'short')
        available_fleet = vehicles.filtered('is_available')

        vehicle_model_data = {}
        transfer_state_data = {}
        for vehicle in vehicles:
            label = vehicle.model_id.display_name or vehicle.name or 'Unspecified'
            vehicle_model_data[label] = vehicle_model_data.get(label, 0) + 1
        state_labels = dict(self.env['stock.picking']._fields['state'].selection)
        for transfer in transfers:
            label = state_labels.get(transfer.state, transfer.state)
            transfer_state_data[label] = transfer_state_data.get(label, 0) + 1

        total_odo = sum(vehicles.mapped('odometer'))
        total_payload = sum(vehicles.mapped('allowable_payload'))
        delivered_volume = sum(done_transfers.mapped('actual_qty'))
        completion_rate = (len(done_transfers) / len(transfers) * 100) if transfers else 0.0

        res['tiles'].extend([
            {
                'id': 'active_transfers',
                'label': 'Active Transfers',
                'value': len(active_transfers),
                'icon': 'fa-random',
                'color': '#0f766e',
                'action': 'oil_erp_transfers.action_oil_gas_transfer',
            },
            {
                'id': 'short_deliveries',
                'label': 'Short Deliveries',
                'value': len(short_deliveries),
                'icon': 'fa-exclamation-circle',
                'color': '#dc2626',
                'action': 'oil_erp_transfers.action_oil_gas_transfer',
            },
        ])

        res['charts'].extend([
            {
                'id': 'fleet_distribution',
                'title': 'Fleet Distribution by Model',
                'type': 'doughnut',
                'width': 5,
                'data': {
                    'labels': list(vehicle_model_data.keys()),
                    'datasets': [{
                        'data': list(vehicle_model_data.values()),
                        'backgroundColor': ['#2563eb', '#7c3aed', '#f59e0b', '#dc2626', '#14b8a6'],
                    }],
                },
            },
            {
                'id': 'transfer_state_mix',
                'title': 'Transfer Execution Status',
                'type': 'bar',
                'width': 7,
                'data': {
                    'labels': list(transfer_state_data.keys()),
                    'datasets': [{
                        'label': 'Transfers',
                        'data': list(transfer_state_data.values()),
                        'backgroundColor': '#0f766e',
                    }],
                },
            },
        ])

        res['metrics'].extend([
            {
                'id': 'fleet_availability',
                'label': 'Fleet Availability',
                'value': f"{(len(available_fleet) / len(vehicles) * 100) if vehicles else 0:.1f}%",
                'description': 'Share of fleet currently marked available for dispatch.',
            },
            {
                'id': 'total_odometer',
                'label': 'Aggregate Fleet Mileage',
                'value': f"{total_odo:,.0f} KM",
                'description': 'Total odometer reading across the oil and gas fleet.',
            },
            {
                'id': 'payload_capacity',
                'label': 'Total Allowable Payload',
                'value': f"{total_payload:,.0f}",
                'description': 'Combined legal carrying capacity across active fleet assets.',
            },
            {
                'id': 'transfer_completion',
                'label': 'Transfer Completion Rate',
                'value': f"{completion_rate:.1f}%",
                'description': 'Completed transfers as a share of all tracked internal transfers.',
            },
            {
                'id': 'delivered_volume',
                'label': 'Confirmed Delivered Quantity',
                'value': f"{delivered_volume:,.2f}",
                'description': 'Actual delivered quantity recorded on completed transfers.',
            },
        ])

        res['highlights'].append({
            'id': 'midstream_dispatch',
            'title': 'Dispatch Snapshot',
            'items': [
                {'label': 'Fleet available', 'value': len(available_fleet)},
                {'label': 'Active transfers', 'value': len(active_transfers)},
                {'label': 'Completed transfers', 'value': len(done_transfers)},
                {'label': 'Short deliveries', 'value': len(short_deliveries)},
            ],
        })

        return res
