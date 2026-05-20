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


class OilDashboardUpstream(models.TransientModel):
    """Extends the upstream dashboard with oil and gas project and well metrics."""

    _inherit = 'oil.dashboard.upstream'

    @api.model
    def get_dashboard_data(self):
        """Compile project and well statistics for the upstream dashboard."""
        res = super().get_dashboard_data()

        project_model = self.env['project.project']
        well_model = self.env['project.task']

        projects = project_model.search([('is_oil_gas_project', '=', True)])
        wells = well_model.search([('is_oil_gas_well', '=', True)])

        active_projects = projects.filtered('active')
        producing_wells = wells.filtered(lambda well: well.stage_id.is_production)
        identified_wells = wells.filtered('well_api_number')

        project_fluid_mix = {}
        for project in projects:
            label = project.primary_fluid_type_id.name or 'Unspecified'
            project_fluid_mix[label] = project_fluid_mix.get(label, 0) + 1

        well_stage_mix = {}
        for well in wells:
            label = well.stage_id.name or 'Unassigned'
            well_stage_mix[label] = well_stage_mix.get(label, 0) + 1

        field_coverage = len({
            field_name for field_name in projects.mapped('field_name') if field_name
        })
        avg_wells_per_project = len(wells) / len(projects) if projects else 0.0
        avg_depth = sum(wells.mapped('total_depth_ft')) / len(wells) if wells else 0.0
        api_coverage = (len(identified_wells) / len(wells) * 100) if wells else 0.0

        res['tiles'].extend([
            {
                'id': 'upstream_projects',
                'label': 'Oil & Gas Projects',
                'value': len(projects),
                'icon': 'fa-sitemap',
                'color': '#0f766e',
                'action': 'oil_erp_project.open_view_project_oil',
            },
            {
                'id': 'upstream_wells',
                'label': 'Tracked Wells',
                'value': len(wells),
                'icon': 'fa-map-pin',
                'color': '#2563eb',
                'action': 'oil_erp_project.action_open_oil_wells',
            },
            {
                'id': 'upstream_producing_wells',
                'label': 'Producing Wells',
                'value': len(producing_wells),
                'icon': 'fa-line-chart',
                'color': '#ea580c',
                'action': 'oil_erp_project.action_open_oil_wells',
            },
        ])

        res['charts'].extend([
            {
                'id': 'project_fluid_mix',
                'title': 'Project Mix by Primary Fluid',
                'type': 'doughnut',
                'width': 6,
                'data': {
                    'labels': list(project_fluid_mix.keys()),
                    'datasets': [{
                        'data': list(project_fluid_mix.values()),
                        'backgroundColor': ['#0f766e', '#2563eb', '#ea580c', '#94a3b8'],
                    }],
                },
            },
            {
                'id': 'well_stage_mix',
                'title': 'Well Lifecycle by Stage',
                'type': 'bar',
                'width': 6,
                'data': {
                    'labels': list(well_stage_mix.keys()),
                    'datasets': [{
                        'label': 'Wells',
                        'data': list(well_stage_mix.values()),
                        'backgroundColor': '#2563eb',
                    }],
                },
            },
        ])

        res['metrics'].extend([
            {
                'id': 'upstream_active_projects',
                'label': 'Active Oil & Gas Projects',
                'value': len(active_projects),
                'description': 'Projects flagged as oil and gas operations and currently active.',
            },
            {
                'id': 'upstream_wells_per_project',
                'label': 'Average Wells per Project',
                'value': f"{avg_wells_per_project:.2f}",
                'description': 'Average well count across tracked oil and gas projects.',
            },
            {
                'id': 'upstream_avg_depth',
                'label': 'Average Well Depth',
                'value': f"{avg_depth:,.0f} ft",
                'description': 'Average total depth captured on oil and gas wells.',
            },
            {
                'id': 'upstream_api_coverage',
                'label': 'API / UWI Coverage',
                'value': f"{api_coverage:.1f}%",
                'description': 'Share of tracked wells with an API or UWI number recorded.',
            },
        ])

        res['highlights'].append({
            'id': 'upstream_project_snapshot',
            'title': 'Project & Well Snapshot',
            'items': [
                {'label': 'Active projects', 'value': len(active_projects)},
                {'label': 'Producing wells', 'value': len(producing_wells)},
                {'label': 'Covered fields', 'value': field_coverage},
                {'label': 'Wells without API', 'value': len(wells) - len(identified_wells)},
            ],
        })

        return res
