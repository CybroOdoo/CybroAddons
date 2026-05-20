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


class OilDashboardDownstream(models.TransientModel):
    _inherit = 'oil.dashboard.downstream'

    @api.model
    def get_dashboard_data(self):
        """Extend the downstream dashboard with quality inspection metrics and statistics."""
        res = super().get_dashboard_data()

        inspections = self.env['oil.inspection.order'].search([])
        pending = inspections.filtered(lambda inspection: inspection.state in ('draft', 'in_progress'))
        completed = inspections.filtered(lambda inspection: inspection.state in ('passed', 'failed'))
        passed = inspections.filtered(lambda inspection: inspection.state == 'passed')
        failed = inspections.filtered(lambda inspection: inspection.state == 'failed')

        quality_rate = (len(passed) / len(completed) * 100) if completed else 0.0
        fail_rate = (len(failed) / len(completed) * 100) if completed else 0.0

        state_data = {
            'Passed': len(passed),
            'Failed': len(failed),
            'Pending': len(pending),
        }

        inspector_data = {}
        product_data = {}
        for inspection in inspections:
            inspector = inspection.responsible_id.name or 'Unassigned'
            inspector_data[inspector] = inspector_data.get(inspector, 0) + 1
            product = inspection.product_id.display_name or 'Unspecified'
            product_data[product] = product_data.get(product, 0) + 1

        top_inspectors = sorted(inspector_data.items(), key=lambda item: item[1], reverse=True)[:5]
        top_products = sorted(product_data.items(), key=lambda item: item[1], reverse=True)[:5]

        inspection_action = self.env['ir.actions.act_window']._for_xml_id('oil_erp_inspection.action_oil_inspection_order')

        pending_action = dict(inspection_action)
        pending_action.update({
            'name': 'Pending Inspections',
            'domain': [('state', 'in', ['draft', 'in_progress'])],
            'context': "{}",
        })

        failed_action = dict(inspection_action)
        failed_action.update({
            'name': 'Failed Inspections',
            'domain': [('state', '=', 'failed')],
            'context': "{}",
        })

        passed_action = dict(inspection_action)
        passed_action.update({
            'name': 'Passed Inspections',
            'domain': [('state', '=', 'passed')],
            'context': "{}",
        })

        res['tiles'].extend([
            {
                'id': 'inspection_pending',
                'label': 'Pending Inspections',
                'value': len(pending),
                'icon': 'fa-clock-o',
                'color': '#f59e0b',
                'action': pending_action,
            },
            {
                'id': 'inspection_failed',
                'label': 'Failed Inspections',
                'value': len(failed),
                'icon': 'fa-times-circle',
                'color': '#dc2626',
                'action': failed_action,
            },
            {
                'id': 'inspection_quality',
                'label': 'Quality Pass Rate',
                'value': f"{quality_rate:.1f}%",
                'icon': 'fa-shield',
                'color': '#0f766e',
                'action': passed_action,
            },
        ])

        res['charts'].extend([
            {
                'id': 'inspection_outcomes',
                'title': 'Inspection Outcomes',
                'type': 'bar',
                'width': 5,
                'data': {
                    'labels': list(state_data.keys()),
                    'datasets': [{
                        'label': 'Inspection Orders',
                        'data': list(state_data.values()),
                        'backgroundColor': ['#16a34a', '#dc2626', '#f59e0b'],
                    }],
                },
            },
            {
                'id': 'inspection_products',
                'title': 'Most Inspected Products',
                'type': 'bar',
                'width': 7,
                'data': {
                    'labels': [label for label, _count in top_products],
                    'datasets': [{
                        'label': 'Inspections',
                        'data': [count for _label, count in top_products],
                        'backgroundColor': '#2563eb',
                    }],
                },
            },
        ])

        res['metrics'].extend([
            {
                'id': 'quality_rate',
                'label': 'Quality Pass Rate',
                'value': f"{quality_rate:.1f}%",
                'description': 'Share of completed inspections that ended in pass status.',
            },
            {
                'id': 'fail_rate',
                'label': 'Inspection Failure Rate',
                'value': f"{fail_rate:.1f}%",
                'description': 'Share of completed inspections ending in failure.',
            },
            {
                'id': 'inspector_coverage',
                'label': 'Active Inspectors',
                'value': len(inspector_data),
                'description': 'Number of inspectors represented in current inspection records.',
            },
        ])

        res['highlights'].extend([
            {
                'id': 'inspection_workload',
                'title': 'Inspection Workload',
                'items': [
                    {'label': 'Total orders', 'value': len(inspections)},
                    {'label': 'Pending', 'value': len(pending)},
                    {'label': 'Passed', 'value': len(passed)},
                    {'label': 'Failed', 'value': len(failed)},
                ],
            },
            {
                'id': 'inspection_top_inspectors',
                'title': 'Top Inspectors',
                'items': [
                    {'label': label, 'value': count}
                    for label, count in top_inspectors
                ] or [{'label': 'No inspector data', 'value': 0}],
            },
        ])

        return res
