#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Report lines of the sales performance report."""
from odoo import fields, models
from odoo.exceptions import UserError


class SalesPerformanceLine(models.TransientModel):
    """One report row (salesperson), owned by one wizard run."""

    _name = 'sales.performance.line'
    _description = "Sales Performance Line"
    _order = 'team_id, user_id'

    wizard_id = fields.Many2one(
        comodel_name='sales.performance',
        required=True,
        index=True,
        ondelete='cascade',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Sales Person',
        readonly=True,
        ondelete='cascade',
    )
    team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Sales Team',
        readonly=True,
        ondelete='set null',
        help='Main sales team of the sales person',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        readonly=True,
    )
    estimated_revenue = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        help='Total of the quotations and sales orders (cancelled excluded)',
    )
    net_revenue = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        help='Total of the confirmed sales orders',
    )
    total_sale_order = fields.Integer(
        string="Total Order",
        readonly=True,
        help='Number of quotations and sales orders (cancelled excluded)',
    )
    sale_order_done = fields.Integer(
        readonly=True,
        help='Number of confirmed sales orders',
    )
    returned_orders = fields.Integer(
        readonly=True,
        help='Number of orders with at least one return',
    )
    avg_price = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        help='Average amount of an order',
    )
    overall_performance = fields.Float(
        string="Overall %",
        readonly=True,
        help='Share of the orders of the period handled by the sales person',
    )
    overall_performance_separate = fields.Float(
        string="Overall Separated",
        readonly=True,
        help='Share of the orders of the period that the sales person '
             'handled for a sales team other than his own',
    )

    def action_sale_order(self):
        """Open the sale orders behind this line.

        :return: action opening sale order list and form views
        :raises UserError: when the user can see no order for the line
        """
        self.ensure_one()
        wizard = self.wizard_id
        domain = wizard._get_order_domain(
            wizard._get_scope_companies(), self.user_id)
        orders = self.env['sale.order'].search(domain)
        if not orders:
            raise UserError(self.env._(
                "No Orders done by this Sales Person!"))
        return {
            'name': self.env._('Sales Order Report'),
            'res_model': 'sale.order',
            'views': [(False, 'list'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', orders.ids)],
        }
