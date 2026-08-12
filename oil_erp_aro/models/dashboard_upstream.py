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
# ############################################################################

from odoo import api, models

class OilDashboardUpstream(models.TransientModel):
    _inherit = 'oil.dashboard.upstream'

    @api.model
    def get_dashboard_data(self):
        """Executes the 'get dashboard data' process within the operational workflow."""
        res = super().get_dashboard_data()
        
        aros = self.env['oil.aro.obligation'].search([])
        total_liability = sum(aros.mapped('current_liability_balance'))
        executing_count = len(aros.filtered(lambda a: a.state == 'executing'))
        active_wip = sum(aros.filtered(lambda a: a.state == 'executing').mapped('wip_total'))

        # Chart: Liability by Asset Kind
        kind_data = {}
        for aro in aros.filtered(lambda a: a.state in ('recognized', 'executing', 'hold')):
            label = dict(aro._fields['asset_kind'].selection).get(aro.asset_kind, 'Unknown')
            kind_data[label] = kind_data.get(label, 0.0) + aro.current_liability_balance

        res['tiles'].extend([
            {
                'id': 'aro_total_liability',
                'label': 'Total ARO Liability',
                'value': f"${total_liability:,.2f}",
                'icon': 'fa-balance-scale',
                'color': '#7c3aed',
                'action': 'oil_erp_aro.action_oil_aro_obligation',
            },
            {
                'id': 'aro_decom_wip',
                'label': 'Decommissioning WIP',
                'value': f"${active_wip:,.2f}",
                'icon': 'fa-cogs',
                'color': '#b91c1c',
                'action': 'oil_erp_aro.action_oil_aro_wip',
            }
        ])

        if kind_data:
            res['charts'].append({
                'id': 'aro_liability_by_kind',
                'title': 'ARO Liability by Asset Kind',
                'type': 'pie',
                'width': 6,
                'data': {
                    'labels': list(kind_data.keys()),
                    'datasets': [{
                        'data': list(kind_data.values()),
                        'backgroundColor': ['#7c3aed', '#0f766e', '#ea580c', '#3b82f6', '#10b981'],
                    }],
                },
            })

        res['metrics'].extend([
            {
                'id': 'aro_executing_count',
                'label': 'Decommissioning Obligations Executing',
                'value': str(executing_count),
                'description': 'Number of active ARO obligations currently in execution.',
            },
            {
                'id': 'aro_active_wip_metric',
                'label': 'Accumulated Decommissioning WIP',
                'value': f"${active_wip:,.2f}",
                'description': 'Total WIP costs recorded for executing obligations.',
            }
        ])

        res['highlights'].append({
            'id': 'aro_health_snapshot',
            'title': 'ARO & Decommissioning Portfolio',
            'items': [
                {'label': 'Total obligations', 'value': len(aros)},
                {'label': 'Currently on hold', 'value': len(aros.filtered(lambda a: a.state == 'hold'))},
                {'label': 'Total recognized liability', 'value': f"${total_liability:,.0f}"},
                {'label': 'Total WIP balance', 'value': f"${active_wip:,.0f}"},
            ],
        })

        return res
