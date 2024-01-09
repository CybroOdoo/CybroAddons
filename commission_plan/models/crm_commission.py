# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhin K(odoo@cybrosys.com)
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
from odoo import api, Command, exceptions, fields, models, _


class CommissionPlan(models.Model):
    """crm.commission plan model is defined here"""
    _name = 'crm.commission'
    _description = 'Commission Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True, help='Name of the Commission')
    active = fields.Boolean('Active', default=True, help='Active or not')
    date_from = fields.Date(string="From Date", required=True,
                            help='Start date of the commission plan')
    date_to = fields.Date(string="To Date", required=True,
                          help='End date of the commission plan')
    type = fields.Selection(
        [('product', 'Product wise'),
         ('revenue', 'Revenue wise')], string="Type",
        default="product", help='Type of the Plan')
    team_id = fields.Many2one('crm.team', string='Sales Team',
                              help='Select the Sales team')
    user_id = fields.Many2one('res.users', string='Salesperson',
                              help='Select the Sales Person')
    product_comm_ids = fields.One2many('commission.product', 'commission_id',
                                       string="Product Wise",
                                       help='Relational field of commission'
                                            ' product')
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id,
                                  help='Currency of the company')
    straight_commission_type = fields.Selection([('percentage', 'Percentage'),
                                                 ('fixed', 'Fixed Amount')],
                                                string="Amount Type",
                                                default='percentage',
                                                help='Straight commission Type')
    straight_commission_fixed = fields.Monetary('Commission Amount',
                                                default=0.0,
                                                help='Straight commission'
                                                     ' fixed amount')
    straight_commission_rate = fields.Float(string='Commission rate (%)',
                                            help='Straight Commission Rate')
    revenue_grd_comm_ids = fields.One2many(
        'commission.graduated',
        'commission_id',
        string="Revenue Graduated Wise",
        help='Relational Commission Graduated')

    revenue_type = fields.Selection(
        [('straight', 'Straight Commission'),
         ('graduated', 'Graduated Commission')],
        string="Revenue Type",
        help='Select the Revenue Type')

    @api.constrains("date_from", "date_to")
    def _check_date(self):
        """Date constraints"""
        for rec in self:
            if rec.date_to < rec.date_from:
                raise exceptions.ValidationError(
                    _("The From date cannot be earlier than To date."))

    @api.onchange('type')
    def _onchange_type(self):
        """onchange type the corresponding table
        is shown and the other table set to hide"""
        if self.type == 'revenue':
            self.product_comm_ids = [Command.clear()]
        elif self.type == 'product':
            self.revenue_type = False
            self.straight_commission_rate = False
            self.revenue_grd_comm_ids = [Command.clear()]
