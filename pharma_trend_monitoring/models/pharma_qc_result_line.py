# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models

from .pharma_trend_parameter import parameter_key


class PharmaQcResultLine(models.Model):
    """Flags a result that falls outside the approved normal range."""
    _inherit = 'pharma.qc.result.line'

    is_trended = fields.Boolean(
        related='parameter_id.is_trended',
        string='Watched',
        help='The specification marks this parameter as watched.',
    )
    trend_parameter_id = fields.Many2one(
        comodel_name='pharma.trend.parameter',
        string='Trended Parameter',
        compute='_compute_outside_normal_range',
        store=True,
        index=True,
        help='History this result belongs to.',
    )
    outside_normal_range = fields.Boolean(
        compute='_compute_outside_normal_range',
        store=True,
        help='The result passes its specification but lies outside the normal '
             'range QA approved for this parameter.',
    )
    # Snapshot of the range in force when the result was evaluated, like the
    # instrument calibration snapshot: a later re-approval does not move it.
    normal_range_applied = fields.Boolean(
        compute='_compute_normal_range_applied',
        store=True,
        help='A normal range was in force when the result was evaluated.',
    )
    normal_range_low = fields.Float(
        string='Normal Range Low (Applied)',
        digits=(16, 4),
        compute='_compute_normal_range_applied',
        store=True,
        help='Lower end of the normal range in force when the result was evaluated.',
    )
    normal_range_high = fields.Float(
        string='Normal Range High (Applied)',
        digits=(16, 4),
        compute='_compute_normal_range_applied',
        store=True,
        help='Upper end of the normal range in force when the result was evaluated.',
    )

    # Only the result itself triggers a re-evaluation: approving a range later
    # never re-flags results that were already reviewed.
    @api.depends('actual_value', 'result_entered', 'parameter_id')
    def _compute_outside_normal_range(self):
        """Compare the entered value with the approved normal range."""
        Parameter = self.env['pharma.trend.parameter'].sudo()
        for line in self:
            param = Parameter
            spec_line = line.parameter_id
            if spec_line.is_trended:
                company = line.test_order_id.lot_id.company_id or self.env.company
                param = Parameter.search([
                    ('company_id', '=', company.id),
                    ('product_id', '=', spec_line.spec_id.product_id.id),
                    ('stage', '=', spec_line.spec_id.stage),
                    ('parameter_key', '=', parameter_key(spec_line.parameter_name)),
                ], limit=1)
            line.trend_parameter_id = param
            line.outside_normal_range = bool(
                param and line.result_entered and param._pharma_is_outside(line.actual_value))

    # Same triggers as the flag, kept in its own method so adding these
    # columns never re-evaluates the flags of results already reviewed.
    @api.depends('actual_value', 'result_entered', 'trend_parameter_id')
    def _compute_normal_range_applied(self):
        """Record the normal range the result was compared with."""
        for line in self:
            param = line.trend_parameter_id
            applied = bool(param and line.result_entered and param.state == 'active')
            line.normal_range_applied = applied
            line.normal_range_low = param.range_low if applied else 0.0
            line.normal_range_high = param.range_high if applied else 0.0
