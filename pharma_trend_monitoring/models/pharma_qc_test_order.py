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
from odoo.exceptions import ValidationError


class PharmaQcTestOrder(models.Model):
    """Carries the outside-normal-range flag and QA's note on it."""
    _inherit = 'pharma.qc.test.order'

    outside_normal_range = fields.Boolean(
        compute='_compute_outside_normal_range',
        store=True,
        help='At least one watched result lies outside its approved normal range.',
    )
    normal_range_note = fields.Text(
        string='QA Note on Normal Range',
        tracking=True,
        copy=False,
        help='QA explanation of the result outside the normal range.',
    )
    normal_range_reviewed = fields.Boolean(
        tracking=True,
        copy=False,
        help='QA has reviewed the result outside the normal range. Until '
             'then the test order cannot be approved and the batch stays on hold.',
    )

    @api.depends('result_line_ids.outside_normal_range')
    def _compute_outside_normal_range(self):
        """Roll the line flags up to the order."""
        for order in self:
            order.outside_normal_range = any(order.result_line_ids.mapped('outside_normal_range'))

    @api.constrains('normal_range_reviewed', 'normal_range_note')
    def _check_normal_range_note(self):
        """A review is ticked with the explanation written."""
        for order in self:
            if order.normal_range_reviewed and not (order.normal_range_note or '').strip():
                raise ValidationError(self.env._(
                    'Write a line explaining the result outside the normal '
                    'range before ticking it reviewed.'))

    def action_approve(self):
        """Hold the batch while a result outside the normal range is not reviewed."""
        unreviewed = self.filtered(
            lambda o: o.outside_normal_range and not o.normal_range_reviewed)
        if unreviewed:
            raise ValidationError(self.env._(
                'Test order %(orders)s cannot be approved: a result is outside '
                'its normal range. QA must write a note and tick it reviewed '
                'first; until then the batch stays on hold.',
                orders=', '.join(unreviewed.mapped('name'))))
        return super().action_approve()

    def write(self, vals):
        """Only QA reviews a result outside the normal range."""
        if not self.env.su and {'normal_range_note', 'normal_range_reviewed'} & set(vals):
            self._check_pharma_group(
                'pharmaceutical_base.group_pharma_role_qa',
                self.env._('Only QA can review a result outside the normal range.'),
            )
        return super().write(vals)
