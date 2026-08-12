# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################

from odoo import api, fields, models


class AccountDashboardConfig(models.Model):
    """Accounting Dashboard User Configuration Model."""
    _name = 'account.dashboard.config'
    _description = 'Accounting Dashboard User Configuration'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        ondelete='cascade',
        index=True,
    )
    layout_config = fields.Json(
        string='Layout Configuration',
        default=dict,
        help='Widget positions, sizes and arrangement (persisted layout)',
    )
    default_period = fields.Selection(
        selection=[
            ('this_month', 'This Month'),
            ('last_month', 'Last Month'),
            ('this_quarter', 'This Quarter'),
            ('last_quarter', 'Last Quarter'),
            ('this_year', 'This Year'),
            ('last_year', 'Last Year'),
            ('custom', 'Custom Range'),
        ],
        string='Default Period',
        help='Default Period',
        default='this_month',
    )
    amount_format = fields.Selection(
        selection=[
            ('full', 'Full'),
            ('K', 'Thousands (K)'),
            ('M', 'Millions (M)'),
            ('B', 'Billions (B)'),
        ],
        string='Amount Format',
        help='Amount Format',
        default='full',
    )
    date_from = fields.Date(string='From Date', help='From Date')
    date_to = fields.Date(string='To Date', help='To Date')
    company_ids = fields.Many2many(
        'res.company',
        string='Companies',
        default=lambda self: self.env.company,
        help='Companies to include in dashboard data',
    )
    collapsed_widgets = fields.Json(
        string='Collapsed Widgets',
        default=list,
        help='List of widget IDs the user has collapsed',
    )
    hidden_kpis = fields.Json(
        string='Hidden KPIs',
        default=list,
        help='List of KPI keys the user has hidden',
    )
    kpi_order = fields.Json(
        string='KPI Order',
        default=list,
        help='Ordered list of KPI keys for display order',
    )
    hidden_charts = fields.Json(
        string='Hidden Charts',
        default=list,
        help='List of chart keys the user has hidden',
    )
    chart_order = fields.Json(
        string='Chart Order',
        default=list,
        help='Ordered list of chart keys for display order',
    )
    theme = fields.Selection(
        selection=[
            ('light', 'Light'),
            ('dark', 'Dark'),
        ],
        string='Theme',
        help='Theme Mode',
        default='dark',
    )

    _sql_constraints = [
        ('user_uniq', 'unique (user_id)', 'Each user can have only one dashboard configuration.')
    ]

    @api.model
    def get_or_create_config(self):
        """Get the current user's dashboard config, creating one if needed."""
        config = self.search([('user_id', '=', self.env.user.id)], limit=1)
        if not config:
            config = self.create({'user_id': self.env.user.id})
        return {
            'id': config.id,
            'default_period': config.default_period,
            'amount_format': config.amount_format,
            'date_from': config.date_from,
            'date_to': config.date_to,
            'company_ids': config.company_ids.ids,
            'collapsed_widgets': config.collapsed_widgets or [],
            'hidden_kpis': config.hidden_kpis or [],
            'kpi_order': config.kpi_order or [],
            'hidden_charts': config.hidden_charts or [],
            'chart_order': config.chart_order or [],
            'layout_config': config.layout_config or {},
            'theme': config.theme,
        }

    def save_config(self, vals):
        """Save dashboard configuration for the current user."""
        self.ensure_one()
        writable = {}
        for key in ('default_period', 'amount_format', 'date_from', 'date_to',
                    'collapsed_widgets', 'hidden_kpis', 'kpi_order',
                    'hidden_charts', 'chart_order',
                    'layout_config', 'theme'):
            if key in vals:
                writable[key] = vals[key]
        if 'company_ids' in vals:
            writable['company_ids'] = [(6, 0, vals['company_ids'])]
        if writable:
            self.write(writable)
        return True
