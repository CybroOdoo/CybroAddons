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
    _inherit = 'oil.dashboard.upstream'

    @api.model
    def get_dashboard_data(self):
        """Extend the upstream dashboard with lease portfolio metrics, charts, and watchlist data."""
        res = super().get_dashboard_data()

        leases = self.env['oil.lease.agreement'].search([])
        today = fields.Date.today()
        active_leases = leases.filtered(lambda lease: lease.state == 'active')
        expiring_soon = active_leases.filtered(
            lambda lease: lease.end_date and 0 <= (lease.end_date - today).days <= 90
        )
        renewable = active_leases.filtered('renewal_option')
        total_acreage = sum(active_leases.mapped('acreage'))

        state_labels = dict(self.env['oil.lease.agreement']._fields['state'].selection)
        state_data = {}
        land_data = {'Onshore': 0, 'Offshore': 0, 'Unspecified': 0}
        for lease in leases:
            state_label = state_labels.get(lease.state, 'Unknown')
            state_data[state_label] = state_data.get(state_label, 0) + 1
            if lease.land_type == 'onshore':
                land_data['Onshore'] += 1
            elif lease.land_type == 'offshore':
                land_data['Offshore'] += 1
            else:
                land_data['Unspecified'] += 1

        avg_acreage = total_acreage / len(active_leases) if active_leases else 0.0

        res['tiles'].extend([
            {
                'id': 'lease_active',
                'label': 'Active Leases',
                'value': len(active_leases),
                'icon': 'fa-file-text-o',
                'color': '#f59e0b',
                'action': 'oil_erp_lease.action_oil_lease_agreement',
            },
            {
                'id': 'lease_expiring',
                'label': 'Expiring in 90 Days',
                'value': len(expiring_soon),
                'icon': 'fa-clock-o',
                'color': '#dc2626',
                'action': 'oil_erp_lease.action_oil_lease_agreement',
            },
        ])

        res['charts'].extend([
            {
                'id': 'lease_status',
                'title': 'Lease Portfolio Status',
                'type': 'doughnut',
                'width': 6,
                'data': {
                    'labels': list(state_data.keys()),
                    'datasets': [{
                        'data': list(state_data.values()),
                        'backgroundColor': ['#f59e0b', '#16a34a', '#dc2626', '#64748b'],
                    }],
                },
            },
            {
                'id': 'lease_land_mix',
                'title': 'Lease Mix by Land Type',
                'type': 'bar',
                'width': 6,
                'data': {
                    'labels': list(land_data.keys()),
                    'datasets': [{
                        'label': 'Leases',
                        'data': list(land_data.values()),
                        'backgroundColor': ['#2563eb', '#0f766e', '#94a3b8'],
                    }],
                },
            },
        ])

        res['metrics'].extend([
            {
                'id': 'total_acreage',
                'label': 'Total Active Acreage',
                'value': f"{total_acreage:,.2f} Acres",
                'description': 'Land currently covered by active lease agreements.',
            },
            {
                'id': 'avg_acreage',
                'label': 'Average Active Lease Size',
                'value': f"{avg_acreage:,.2f} Acres",
                'description': 'Average acreage size across all active leases.',
            },
            {
                'id': 'renewable_share',
                'label': 'Renewal Ready Share',
                'value': f"{(len(renewable) / len(active_leases) * 100) if active_leases else 0:.1f}%",
                'description': 'Share of active leases that already have renewal options enabled.',
            },
        ])

        res['highlights'].append({
            'id': 'lease_watchlist',
            'title': 'Lease Watchlist',
            'items': [
                {'label': 'Portfolio size', 'value': len(leases)},
                {'label': 'Active leases', 'value': len(active_leases)},
                {'label': 'Expiring soon', 'value': len(expiring_soon)},
                {'label': 'Renewal enabled', 'value': len(renewable)},
            ],
        })

        return res
