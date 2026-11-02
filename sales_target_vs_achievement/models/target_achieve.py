# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class TargetAchieve(models.Model):
    """Model for sales targets and achievements"""
    _name = 'target.achieve'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Target Achieve'

    name = fields.Char(compute='_compute_name', store=True,
                       help="Automatically generated name, combining the "
                            "salesperson and the sales team.")

    sale_user_id = fields.Many2one('crm.team.member',
                                   string="Salesperson", required=True,
                                   tracking=True,
                                   help="Team member to whom the target is assigned.")
    user_target = fields.Float('Salesperson Target', required=True,
                               tracking=True,
                               help="Personal target amount the salesperson should reach.",
                               copy=False)
    time_span = fields.Selection(
        [('daily', 'Daily'),
         ('monthly', 'Monthly'),
         ('yearly', 'Yearly')], default='monthly',
        required=True, tracking=True,
        help="Choose whether the target is daily, monthly or yearly.")
    team_id = fields.Many2one('crm.team',
                              related='sale_user_id.crm_team_id',
                              string="Sales Team",
                              help="Sales team of which the salesperson is a member.",
                              store=True)
    team_target = fields.Float(related='team_id.team_target',
                               help="Automatically calculated target of the sales team.")
    person_achieved_amt = fields.Float(string='Person Achieved Amount',
                                       help="Automatically calculated from the confirmed "
                                            "sales orders of each salesperson.",
                                       compute='_compute_person_achieved_amt',
                                       compute_sudo=True)
    team_achieved_amt = fields.Float(string='Team Achieved Amount',
                                     store=True,
                                     compute_sudo=True,
                                     help="Automatically calculated from the confirmed "
                                          "sales orders of each sales team.",
                                     compute='_compute_team_achieved_amt')
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self:
                                  self.env.company.currency_id,
                                  help="Currency used to display the monetary "
                                       "fields.")
    _unique_combination = models.Constraint(
        'unique (name)',
        "A similar target for the same member already exists.",
    )
    _check_user_target = models.Constraint(
        'CHECK(user_target > 0.0)',
        "The Salesperson Target must be greater than zero.",
    )

    def _get_achieved_domain(self):
        """Return the domain of the confirmed sales orders that fall inside
        the time span of the target."""
        self.ensure_one()
        today = fields.Date.today()
        domain = [('state', '=', 'sale')]
        if self.time_span == 'daily':
            domain.append(('date_order', '>=', today))
        elif self.time_span == 'monthly':
            domain.append(('date_order', '>=', today.replace(day=1)))
        elif self.time_span == 'yearly':
            domain.append(('date_order', '>=', today.replace(month=1, day=1)))
        return domain

    @api.depends('sale_user_id.user_id', 'time_span')
    def _compute_person_achieved_amt(self):
        """Compute the achieved sales amount of the salesperson, based on
        the selected time span."""
        for rec in self:
            user = rec.sale_user_id.user_id
            if not user:
                rec.person_achieved_amt = 0.0
                continue
            domain = rec._get_achieved_domain() + [('user_id', '=', user.id)]
            [(total,)] = self.env['sale.order']._read_group(
                domain, aggregates=['amount_total:sum'])
            rec.person_achieved_amt = total or 0.0

    @api.depends('team_id.target_sale_order_ids.state',
                 'team_id.target_sale_order_ids.amount_total',
                 'team_id.target_sale_order_ids.date_order',
                 'time_span')
    def _compute_team_achieved_amt(self):
        """Compute the achieved sales amount of the sales team, based on the
        selected time span. It is recomputed whenever a sales order of the
        team changes."""
        for rec in self:
            if not rec.team_id:
                rec.team_achieved_amt = 0.0
                continue
            domain = rec._get_achieved_domain() + [
                ('team_id', '=', rec.team_id.id)]
            [(total,)] = self.env['sale.order']._read_group(
                domain, aggregates=['amount_total:sum'])
            rec.team_achieved_amt = total or 0.0

    @api.depends('sale_user_id', 'time_span', 'team_id')
    def _compute_name(self):
        """Compute the record name, which is used to prevent duplicate
        targets."""
        for record in self:
            record.name = f"{record.sale_user_id.name}:{record.team_id.name}"
