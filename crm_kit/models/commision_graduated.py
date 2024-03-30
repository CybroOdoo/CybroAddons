# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import exceptions
from odoo import api, fields, models, _


class CommissionGraduated(models.Model):
    """
    This class represents Commission Revenue Graduated Wise.
    """
    _name = 'commission.graduated'
    _description = 'Commission Revenue Graduated Wise'

    graduated_commission_rate = fields.Float(string='Commission rate (%)',
                                             help="Graduated Commission rate")
    amount_from = fields.Float(string="From Amount", help='Amount from')
    amount_to = fields.Float(string="To Amount", help='Amount to')
    commission_id = fields.Many2one("crm.commission",
                                    string="Commission",
                                    help="Commission for graduation")
    sequence = fields.Integer(string='Sequence', compute='_compute_sequence',
                              store=True, help="sequence")

    @api.depends('commission_id')
    def _compute_sequence(self):
        """
        Add a sequence
        """
        number = 1
        seq = self.mapped('commission_id')
        for rule in seq.revenue_grd_comm_ids:
            rule.sequence = number
            number += 1

    @api.constrains("amount_from", "amount_to")
    def _check_amounts(self):
        """
        Check the validity of 'amount_from' and 'amount_to' values.

        :raise exceptions.ValidationError: If 'amount_to' is less than
        'amount_from'.
        :return: None
        """
        for rec in self:
            if rec.amount_to < rec.amount_from:
                raise exceptions.ValidationError(
                    _("The From Amount limit cannot be greater than To Amount.")
                )
