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
    """Extends the upstream dashboard with royalty payment metrics."""

    _inherit = 'oil.dashboard.upstream'

    @api.model
    def get_dashboard_data(self):
        """Compile royalty statistics including payment totals and status distribution."""
        res = super().get_dashboard_data()

        royalties = self.env['oil.royalty'].search([])
        processed = royalties.filtered(lambda royalty: royalty.state in ('confirmed', 'billed'))
        billed = royalties.filtered(lambda royalty: royalty.state == 'billed')
        draft = royalties.filtered(lambda royalty: royalty.state == 'draft')
        total_paid = sum(processed.mapped('total_royalty_amount'))
        total_revenue = sum(processed.mapped('total_gross_revenue'))
        total_production = sum(processed.mapped('total_production'))

        state_data = {}
        state_labels = dict(self.env['oil.royalty']._fields['state'].selection)
        lease_amounts = {}
        for royalty in royalties:
            state_label = state_labels.get(royalty.state, 'Unknown')
            state_data[state_label] = state_data.get(state_label, 0) + 1
        for royalty in processed:
            lease_name = royalty.lease_id.display_name or 'Unassigned'
            lease_amounts[lease_name] = lease_amounts.get(lease_name, 0.0) + royalty.total_royalty_amount

        top_leases = sorted(lease_amounts.items(), key=lambda item: item[1], reverse=True)[:5]

        res['tiles'].extend([
            {
                'id': 'royalty_billed',
                'label': 'Billed Royalties',
                'value': len(billed),
                'icon': 'fa-file-text-o',
                'color': '#0f766e',
                'action': 'oil_erp_royalty.action_oil_royalty',
            },
        ])

        res['charts'].extend([
            {
                'id': 'royalty_state_mix',
                'title': 'Royalty Processing Status',
                'type': 'doughnut',
                'width': 5,
                'data': {
                    'labels': list(state_data.keys()),
                    'datasets': [{
                        'data': list(state_data.values()),
                        'backgroundColor': ['#f59e0b', '#2563eb', '#16a34a'],
                    }],
                },
            },
            {
                'id': 'royalty_by_lease',
                'title': 'Top Lease Royalty Exposure',
                'type': 'bar',
                'width': 7,
                'data': {
                    'labels': [label for label, _amount in top_leases],
                    'datasets': [{
                        'label': 'Royalty Amount',
                        'data': [amount for _label, amount in top_leases],
                        'backgroundColor': '#16a34a',
                    }],
                },
            },
        ])

        recovery_ratio = (total_paid / total_revenue * 100) if total_revenue else 0.0
        avg_royalty = total_paid / len(processed) if processed else 0.0

        res['metrics'].extend([
            {
                'id': 'total_royalties',
                'label': 'Total Royalties Processed',
                'value': f"$ {total_paid:,.2f}",
                'description': 'Cumulative royalty amount confirmed or billed.',
            },
            {
                'id': 'royalty_revenue_ratio',
                'label': 'Royalty to Revenue Ratio',
                'value': f"{recovery_ratio:.2f}%",
                'description': 'Share of reported gross revenue flowing to royalty obligations.',
            },
            {
                'id': 'avg_royalty',
                'label': 'Average Processed Royalty',
                'value': f"$ {avg_royalty:,.2f}",
                'description': 'Average royalty amount across confirmed and billed records.',
            },
            {
                'id': 'tracked_production',
                'label': 'Production Covered',
                'value': f"{total_production:,.2f}",
                'description': 'Total production volume represented in processed royalties.',
            },
        ])

        res['highlights'].append({
            'id': 'royalty_summary',
            'title': 'Royalty Summary',
            'items': [
                {'label': 'All royalty records', 'value': len(royalties)},
                {'label': 'Processed', 'value': len(processed)},
                {'label': 'Billed', 'value': len(billed)},
                {'label': 'Draft backlog', 'value': len(draft)},
            ],
        })

        return res
