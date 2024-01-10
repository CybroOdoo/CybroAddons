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
from odoo import api, exceptions, fields, models, _


class CommissionGraduated(models.Model):
    """commission.graduated model is defined here"""
    _name = 'commission.graduated'
    _description = 'Commission Revenue Graduated Wise'

    currency_id = fields.Many2one("res.currency", string="Currency",
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id,
                                  help='Currency of the company')
    graduated_amount_type = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed Amount')],
        string="Amount Type", default='percentage',
        help='Graduated Amount Type')
    graduated_fixed_amount = fields.Monetary('Commission Amount', default=0.0,
                                             help='Graduated Fixed Amount')
    graduated_commission_rate = fields.Float(string='Commission rate (%)',
                                             help='Graduated Commission Rate')
    amount_from = fields.Float(string="From Amount", help='The Minimum Amount')
    amount_to = fields.Float(string="To Amount", help='The Maximum Amount')
    commission_id = fields.Many2one("crm.commission", string='Commission',
                                    help='Crm Commission')
    sequence = fields.Integer(string='Sequence', compute='_compute_sequence',
                              store=True, help='Sequence Generator')

    @api.depends('commission_id')
    def _compute_sequence(self):
        """sequence is computed in the one2many table"""
        number = 1
        seq = self.mapped('commission_id')
        for rule in seq.revenue_grd_comm_ids:
            rule.sequence = number
            number += 1

    @api.constrains("amount_from", "amount_to")
    def _check_amounts(self):
        """Amount constraints to check the
        amount to is greater than amount from"""
        for rec in self:
            if rec.amount_to < rec.amount_from:
                raise exceptions.ValidationError(
                    _("The From Amount limit cannot "
                      "be greater than To Amount."))
