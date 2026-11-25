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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Commission Graduated model."""
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class CommissionGraduated(models.Model):
    """This class represents Commission Revenue Graduated Wise."""

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

    @api.depends('commission_id.revenue_grd_comm_ids')
    def _compute_sequence(self):
        """Compute sequence for graduated commission rules."""
        for commission in self.commission_id:
            for number, rule in enumerate(commission.revenue_grd_comm_ids, start=1):
                rule.sequence = number
        for rec in self.filtered(lambda r: not r.commission_id):
            rec.sequence = 1

    @api.constrains("amount_from", "amount_to")
    def _check_amounts(self):
        """Check the validity of 'amount_from' and 'amount_to' values.

        :raise ValidationError: If 'amount_to' is less than 'amount_from'.
        """
        for rec in self:
            if rec.amount_to and rec.amount_from and rec.amount_to < rec.amount_from:
                raise ValidationError(
                    _("The From Amount limit cannot be greater than To Amount.")
                )
