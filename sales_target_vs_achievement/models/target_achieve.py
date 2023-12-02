# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class TargetAchieve(models.Model):
    """Target Achieve class to set the target and compute its achievement
    based on the span given for the CRM Team member and their Team"""
    _name = 'target.achieve'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Target Achieve'

    name = fields.Char(string='Name',
                       help="Auto created name which is a combination"
                            " of Salesperson, timespan and team name.")
    sale_user_id = fields.Many2one('crm.team.member',
                                   string="Salesperson", required=True,
                                   tracking=True,
                                   help="Team member to whom the target is set")
    user_target = fields.Float('Salesperson Target', required=True,
                               tracking=True,
                               help="Value for the personal target to reach.",
                               copy=False)
    time_span = fields.Selection(
        [('daily', 'Daily'),
         ('monthly', 'Monthly'),
         ('yearly', 'Yearly')], string='Time Span', default='monthly',
        required=True, tracking=True,
        help="The target can be set Daily/Monthly/Yearly with this field.")
    team_id = fields.Many2one('crm.team',
                              related='sale_user_id.crm_team_id',
                              string="Sales Team",
                              help="Sales Team in which the user is a member.",
                              store=True)
    team_target = fields.Float(string="Team Target",
                               compute='_compute_team_target',
                               help="Auto calculated value of Sales team.")
    person_achieved_amt = fields.Float(string='Person Achieved Amount',
                                       compute_sudo=True,
                                       help="Auto calculated value taken from"
                                            "sale orders for each Salesperson.",
                                       compute='_compute_achieved_amt')
    team_achieved_amt = fields.Float(string='Team Achieved Amount',
                                     store=True,
                                     compute_sudo=True,
                                     help="Auto calculated value taken from"
                                          "sale orders for each sales team.",
                                     compute='_compute_achieved_amt')
    currency_id = fields.Many2one('res.currency',
                                  string='Currency',
                                  default=lambda self:
                                  self.env.company.currency_id,
                                  help="Company currency field to show the"
                                       " monetary field.")
    _sql_constraints = [
        ('unique_combination', 'unique (name)',
         "Similar Target for the same member already exists."),
        ('check_user_target',
         'CHECK(user_target > 0.0)',
         "The Salesperson Target cannot be zero.",),
    ]

    @api.depends('sale_user_id', 'user_target')
    def _compute_team_target(self):
        """For every change in Salesperson and Target set, the Sales Team
        Target is re-calculated and made visible in Sales Team view"""
        for rec in self:
            for team in self.env['crm.team'].browse(rec.team_id.id):
                team.default_get('team_id')
            rec.team_target = rec.team_target + rec.user_target

    def name_get(self):
        """Set the rec_name so that the similar kind of  Target setting
        can be avoided"""
        result = []
        for record in self:
            record.name = record.sale_user_id.name + ':' + \
                          record.time_span + ':' + record.team_id.name
            result.append((record.id, record.name))
        return result

    @api.depends('sale_user_id', 'time_span', 'team_id')
    def _compute_achieved_amt(self):
        """Compute the Achieved sales amount for Member and Sales Team
        separately  based on the span selected"""
        for rec in self:
            rec.person_achieved_amt = rec.team_achieved_amt = 0.0
            if rec.time_span == 'daily':
                daily_so = self.env['sale.order'].search(
                    [('state', '=', 'sale')]).filtered(
                    lambda x: x.date_order.date() == fields.Date.today())
                orders = daily_so
            elif rec.time_span == 'monthly':
                monthly_so = self.env['sale.order'].search(
                    [('state', '=', 'sale')]).filtered(
                    lambda x: x.date_order.date().month == fields.Date.today().
                    month).filtered(
                    lambda x: x.date_order.date(
                    ).year == fields.Date.today().year)
                orders = monthly_so
            else:
                yearly_so = self.env['sale.order'].search(
                    [('state', '=', 'sale')]).filtered(
                    lambda x: x.date_order.date(
                    ).year == fields.Date.today().year)
                orders = yearly_so
            for order in orders:
                if order.user_id.id == rec.sale_user_id.user_id.id:
                    rec.person_achieved_amt = \
                        rec.person_achieved_amt + order.amount_total
                if order.team_id.id == rec.team_id.id:
                    rec.team_achieved_amt = \
                        rec.team_achieved_amt + order.amount_total

    @api.ondelete(at_uninstall=False)
    def delete_record(self):
        """ Deletion of a record must reset the Sales Team target"""
        for record in self:
            record.team_id.update({
                'team_target': record.team_id.team_target - record.user_target})
