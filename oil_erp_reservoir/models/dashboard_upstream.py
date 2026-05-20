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

from odoo import api, fields, models


class OilDashboardUpstream(models.TransientModel):
    """Extends the upstream dashboard with reservoir metrics and fluid type analysis."""

    _inherit = 'oil.dashboard.upstream'

    @api.model
    def get_dashboard_data(self):
        """Compile reservoir statistics including stage distribution, fluid types, and reserve estimates."""
        res = super().get_dashboard_data()

        reservoirs = self.env['oil.reservoir'].search([])
        project_model = self.env['project.project']
        projects = project_model.search([('is_oil_gas_project', '=', True)])

        active_reservoirs = len(reservoirs.filtered('active'))
        total_reserves = sum(reservoirs.mapped('estimated_reserves'))
        avg_reserves = total_reserves / len(reservoirs) if reservoirs else 0.0
        avg_recovery = sum(reservoirs.mapped('recovery_factor')) / len(reservoirs) if reservoirs else 0.0

        fluid_data = {}
        for reservoir in reservoirs:
            label = reservoir.fluid_type_id.name or 'Unspecified'
            fluid_data[label] = fluid_data.get(label, 0) + 1


        stage_data = {}
        for reservoir in reservoirs:
            label = reservoir.stage_id.name or 'Unassigned'
            stage_data[label] = stage_data.get(label, 0) + 1

        res['tiles'].extend([
            {
                'id': 'reservoir_active',
                'label': 'Active Reservoirs',
                'value': active_reservoirs,
                'icon': 'fa-database',
                'color': '#0f766e',
                'action': 'oil_erp_reservoir.action_oil_reservoir',
            },
            {
                'id': 'upstream_reserves',
                'label': 'Estimated Reserves',
                'value': f"{total_reserves:,.1f} MMboe",
                'icon': 'fa-area-chart',
                'color': '#ea580c',
                'action': 'oil_erp_reservoir.action_oil_reservoir',
            },
        ])

        res['charts'].extend([
            {
                'id': 'reservoir_fluid_types',
                'title': 'Reservoir Mix by Fluid Type',
                'type': 'pie',
                'width': 6,
                'data': {
                    'labels': list(fluid_data.keys()),
                    'datasets': [{
                        'data': list(fluid_data.values()),
                        'backgroundColor': ['#2563eb', '#16a34a', '#f59e0b', '#dc2626', '#7c3aed'],
                    }],
                },
            },
            {
                'id': 'reservoir_stage_mix',
                'title': 'Reservoir Stage Distribution',
                'type': 'bar',
                'width': 6,
                'data': {
                    'labels': list(stage_data.keys()),
                    'datasets': [{
                        'label': 'Reservoirs',
                        'data': list(stage_data.values()),
                        'backgroundColor': '#0f766e',
                    }],
                },
            },
        ])

        res['metrics'].extend([
            {
                'id': 'total_reserves',
                'label': 'Total Estimated Reserves',
                'value': f"{total_reserves:,.2f} MMboe",
                'description': 'Total estimated reserves across all tracked reservoirs.',
            },
            {
                'id': 'avg_reserves',
                'label': 'Average Reserves per Reservoir',
                'value': f"{avg_reserves:,.2f} MMboe",
                'description': 'Mean reserve size of the current upstream portfolio.',
            },
            {
                'id': 'avg_recovery',
                'label': 'Average Recovery Factor',
                'value': f"{avg_recovery:.1f}%",
                'description': 'Average expected recoverability from reservoir data.',
            },
        ])

        res['highlights'].append({
            'id': 'reservoir_health',
            'title': 'Reservoir Health Snapshot',
            'items': [
                {'label': 'Tracked reservoirs', 'value': len(reservoirs)},
                {'label': 'Active reservoirs', 'value': active_reservoirs},
                {'label': 'Oil & gas projects', 'value': len(projects)},
                {'label': 'Average reserves', 'value': f"{avg_reserves:,.1f} MMboe"},
            ],
        })

        return res
