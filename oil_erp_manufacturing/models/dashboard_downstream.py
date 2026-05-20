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


class OilDashboardDownstream(models.TransientModel):
    """Extends the downstream dashboard with manufacturing order metrics."""

    _inherit = 'oil.dashboard.downstream'

    @api.model
    def get_dashboard_data(self):
        """Compile manufacturing order statistics including status distribution, product mix, and completion rates."""
        res = super().get_dashboard_data()

        productions = self.env['mrp.production'].search([])
        active_orders = productions.filtered(lambda order: order.state in ('confirmed', 'progress', 'to_close'))
        done_orders = productions.filtered(lambda order: order.state == 'done')
        today = fields.Date.today()
        late_orders = productions.filtered(
            lambda order: order.state not in ('done', 'cancel')
            and order.date_deadline
            and order.date_deadline < today
        )

        state_labels = dict(self.env['mrp.production']._fields['state'].selection)
        status_data = {}
        product_data = {}
        for order in productions:
            status_label = state_labels.get(order.state, order.state)
            status_data[status_label] = status_data.get(status_label, 0) + 1
            product_label = order.product_id.display_name or 'Unspecified'
            product_data[product_label] = product_data.get(product_label, 0) + 1

        top_products = sorted(product_data.items(), key=lambda item: item[1], reverse=True)[:5]

        total_qty = sum(done_orders.mapped('product_qty'))
        cycle_rate = (len(done_orders) / len(productions) * 100) if productions else 0.0

        mrp_action = self.env['ir.actions.act_window']._for_xml_id('mrp.mrp_production_action')
        today_str = fields.Date.today().strftime('%Y-%m-%d')

        active_action = dict(mrp_action)
        active_action.update({
            'name': 'Active Refining Orders',
            'domain': [('state', 'in', ['confirmed', 'progress', 'to_close'])],
            'context': "{'search_default_todo': False}",
        })

        done_action = dict(mrp_action)
        done_action.update({
            'name': 'Completed Orders',
            'domain': [('state', '=', 'done')],
            'context': "{'search_default_todo': False}",
        })

        late_action = dict(mrp_action)
        late_action.update({
            'name': 'Late Orders',
            'domain': [('state', 'not in', ['done', 'cancel']), ('date_deadline', '<', today_str)],
            'context': "{'search_default_todo': False}",
        })

        res['tiles'].extend([
            {
                'id': 'downstream_mo_active',
                'label': 'Active Refining Orders',
                'value': len(active_orders),
                'icon': 'fa-industry',
                'color': '#0f766e',
                'action': active_action,
            },
            {
                'id': 'downstream_mo_done',
                'label': 'Completed Orders',
                'value': len(done_orders),
                'icon': 'fa-check-circle',
                'color': '#16a34a',
                'action': done_action,
            },
            {
                'id': 'downstream_mo_late',
                'label': 'Late Orders',
                'value': len(late_orders),
                'icon': 'fa-clock-o',
                'color': '#dc2626',
                'action': late_action,
            },
        ])

        res['charts'].extend([
            {
                'id': 'mo_status',
                'title': 'Manufacturing Order Status',
                'type': 'doughnut',
                'width': 5,
                'data': {
                    'labels': list(status_data.keys()),
                    'datasets': [{
                        'data': list(status_data.values()),
                        'backgroundColor': ['#2563eb', '#f59e0b', '#16a34a', '#dc2626', '#64748b'],
                    }],
                },
            },
            {
                'id': 'mo_product_mix',
                'title': 'Top Manufactured Products',
                'type': 'bar',
                'width': 7,
                'data': {
                    'labels': [label for label, _count in top_products],
                    'datasets': [{
                        'label': 'Orders',
                        'data': [count for _label, count in top_products],
                        'backgroundColor': '#0f766e',
                    }],
                },
            },
        ])

        res['metrics'].extend([
            {
                'id': 'mo_active',
                'label': 'Active Manufacturing Orders',
                'value': len(active_orders),
                'description': 'Orders currently waiting, confirmed, or in progress.',
            },
            {
                'id': 'mo_output',
                'label': 'Completed Production Quantity',
                'value': f"{total_qty:,.2f}",
                'description': 'Total finished quantity from completed manufacturing orders.',
            },
            {
                'id': 'mo_completion_rate',
                'label': 'Completion Rate',
                'value': f"{cycle_rate:.1f}%",
                'description': 'Completed manufacturing orders as a share of total tracked orders.',
            },
        ])

        res['highlights'].append({
            'id': 'manufacturing_focus',
            'title': 'Refinery Execution',
            'items': [
                {'label': 'Tracked orders', 'value': len(productions)},
                {'label': 'Active orders', 'value': len(active_orders)},
                {'label': 'Completed orders', 'value': len(done_orders)},
                {'label': 'Late orders', 'value': len(late_orders)},
            ],
        })

        return res
