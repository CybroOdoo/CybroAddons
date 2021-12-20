# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import exceptions
from odoo import fields, models, api, _


class CommissionPlan(models.Model):
    _name = 'crm.commission'
    _description = 'Commission Plan'
    _rec_name = "name"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)
    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True)
    type = fields.Selection(
        [('product', 'Product wise'),
         ('revenue', 'Revenue wise')], string="Type",
        default="product")
    team_id = fields.Many2one('crm.team', string='Sales Team')
    user_id = fields.Many2one('res.users', string='Salesperson')
    product_comm_ids = fields.One2many('commission.product', 'commission_id',
                                       string="Product Wise")
    straight_commission_rate = fields.Float(string='Commission rate (%)')
    revenue_grd_comm_ids = fields.One2many(
        'commission.graduated',
        'commission_id',
        string="Revenue Graduated Wise")

    revenue_type = fields.Selection(
        [('straight', 'Straight Commission'),
         ('graduated', 'Graduated Commission')],
        string="Revenue Type")

    @api.constrains("date_from", "date_to")
    def _check_date(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise exceptions.ValidationError(
                    _("The From date cannot be earlier than To date.")
                )

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'revenue':
            self.product_comm_ids = [(5, 0, 0)]
        elif self.type == 'product':
            self.revenue_type = False
            self.straight_commission_rate = False
            self.revenue_grd_comm_ids = [(5, 0, 0)]


class CommissionProduct(models.Model):
    _name = 'commission.product'
    _description = 'Commission Product Wise'

    user_id = fields.Many2one('res.users')
    category_id = fields.Many2one('product.category', string='Product Category')
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('categ_id', '=', category_id)]")
    percentage = fields.Float(string='Rate in Percentage (%)')
    amount = fields.Monetary('Maximum Commission Amount', default=0.0)
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id)
    commission_id = fields.Many2one("crm.commission")


class CommissionRevenueGraduated(models.Model):
    _name = 'commission.graduated'
    _description = 'Commission Revenue Graduated Wise'

    graduated_commission_rate = fields.Float(string='Commission rate (%)')
    amount_from = fields.Float(string="From Amount")
    amount_to = fields.Float(string="To Amount")
    commission_id = fields.Many2one("crm.commission")
    sequence = fields.Integer(string='Sequence', compute='_compute_sequence',
                              store=True)

    @api.depends('commission_id')
    def _compute_sequence(self):
        number = 1
        seq = self.mapped('commission_id')
        for rule in seq.revenue_grd_comm_ids:
            rule.sequence = number
            number += 1

    @api.constrains("amount_from", "amount_to")
    def _check_amounts(self):
        for rec in self:
            if rec.amount_to < rec.amount_from:
                raise exceptions.ValidationError(
                    _("The From Amount limit cannot be greater than To Amount.")
                )


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    commission_id = fields.Many2one('crm.commission', string='Commission Plan')


class CrmSalespersons(models.Model):
    _inherit = 'res.users'

    commission_id = fields.Many2one('crm.commission', string='Commission Plan')
