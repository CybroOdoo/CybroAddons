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
    """Extends the midstream dashboard with pipeline network and transfer metrics."""

    _inherit = 'oil.dashboard.midstream'

    @api.model
    def get_dashboard_data(self):
        """Compile pipeline carrier, transfer, and performance data for the midstream dashboard."""
        res = super().get_dashboard_data()

        carriers = self.env['delivery.carrier'].search([('is_oil_gas_pipeline', '=', True)])
        pipeline_transfers = self.env['stock.picking'].search([
            ('is_pipeline_transfer', '=', True),
            ('is_oil_gas_transfer', '=', True),
            ('picking_type_code', '=', 'internal'),
        ])

        active_carriers = carriers.filtered('active')
        active_transfers = pipeline_transfers.filtered(lambda picking: picking.state not in ('done', 'cancel'))
        completed_transfers = pipeline_transfers.filtered(lambda picking: picking.state == 'done')

        operator_data = {}
        transfer_mix = {'Pipeline': len(pipeline_transfers), 'Non-Pipeline': 0}
        for carrier in carriers:
            label = carrier.pipeline_operator.display_name or carrier.name or 'Unassigned'
            operator_data[label] = operator_data.get(label, 0) + 1

        non_pipeline = self.env['stock.picking'].search_count([
            ('is_oil_gas_transfer', '=', True),
            ('picking_type_code', '=', 'internal'),
            ('is_pipeline_transfer', '=', False),
        ])
        transfer_mix['Non-Pipeline'] = non_pipeline

        total_capacity = sum(carriers.mapped('max_weight'))
        avg_duration = 0.0
        durations = completed_transfers.filtered(lambda picking: picking.pipeline_delivery_start and picking.pipeline_delivery_end)
        if durations:
            avg_duration = sum(durations.mapped('delivery_duration')) / len(durations)

        res['tiles'].extend([
            {
                'id': 'pipeline_active_transfers',
                'label': 'Pipeline Transfers',
                'value': len(active_transfers),
                'icon': 'fa-sliders',
                'color': '#2563eb',
                'action': 'oil_erp_transfers.action_oil_gas_transfer',
            },
            {
                'id': 'pipeline_completed',
                'label': 'Completed Pipeline Moves',
                'value': len(completed_transfers),
                'icon': 'fa-check-circle',
                'color': '#16a34a',
                'action': 'oil_erp_transfers.action_oil_gas_transfer',
            },
        ])

        res['charts'].extend([
            {
                'id': 'pipeline_operator_mix',
                'title': 'Pipeline Network by Operator',
                'type': 'pie',
                'width': 6,
                'data': {
                    'labels': list(operator_data.keys()),
                    'datasets': [{
                        'data': list(operator_data.values()),
                        'backgroundColor': ['#2563eb', '#0f766e', '#f59e0b', '#dc2626', '#7c3aed'],
                    }],
                },
            },
            {
                'id': 'pipeline_transfer_mix',
                'title': 'Midstream Transfer Mode Split',
                'type': 'bar',
                'width': 6,
                'data': {
                    'labels': list(transfer_mix.keys()),
                    'datasets': [{
                        'label': 'Transfers',
                        'data': list(transfer_mix.values()),
                        'backgroundColor': ['#0f766e', '#94a3b8'],
                    }],
                },
            },
        ])

        res['metrics'].extend([
            {
                'id': 'pipeline_availability',
                'label': 'Active Pipeline Methods',
                'value': len(active_carriers),
                'description': 'Pipeline-enabled delivery methods currently active.',
            },
            {
                'id': 'pipeline_capacity',
                'label': 'Nominal Pipeline Weight Capacity',
                'value': f"{total_capacity:,.0f}",
                'description': 'Sum of max weight configured on pipeline delivery methods.',
            },
            {
                'id': 'pipeline_completion_rate',
                'label': 'Pipeline Completion Rate',
                'value': f"{(len(completed_transfers) / len(pipeline_transfers) * 100) if pipeline_transfers else 0:.1f}%",
                'description': 'Completed pipeline transfers as a share of tracked pipeline movements.',
            },
            {
                'id': 'pipeline_avg_duration',
                'label': 'Average Pipeline Delivery Duration',
                'value': f"{avg_duration:.2f} hrs",
                'description': 'Average duration calculated from completed pipeline transfer timestamps.',
            },
        ])

        res['highlights'].append({
            'id': 'pipeline_focus',
            'title': 'Pipeline Focus',
            'items': [
                {'label': 'Pipeline carriers', 'value': len(carriers)},
                {'label': 'Active pipeline transfers', 'value': len(active_transfers)},
                {'label': 'Completed transfers', 'value': len(completed_transfers)},
                {'label': 'Operator coverage', 'value': len(operator_data)},
            ],
        })

        return res
