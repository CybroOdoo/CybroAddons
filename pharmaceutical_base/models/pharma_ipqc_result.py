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
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class PharmaIPQCResult(models.Model):
    """In-Process Quality Control result recorded at a specific BMR step."""
    _name = 'pharma.ipqc.result'
    _description = 'IPQC In-Process Quality Check'
    _inherit = ['mail.thread']
    _rec_name = 'parameter_id'
    _order = 'bmr_id, id'

    bmr_id = fields.Many2one(
        comodel_name='pharma.bmr',
        string='BMR',
        required=True,
        ondelete='cascade',
        index=True,
            help='Specifies the BMR for this record.',
    )

    step_id = fields.Many2one(
        comodel_name='pharma.bmr.step',
        string='BMR Step',
        required=True,
        domain="[('bmr_id', '=', bmr_id), ('operator_signed_on', '!=', False), ('supervisor_signed_on', '=', False)]",
        ondelete='restrict',
        help='Specifies the BMR Step for this record.',
    )

    @api.constrains('step_id')
    def _check_step_signoff_state(self):
        """IPQC check needs an operator-signed step without supervisor sign-off."""
        for rec in self:
            if not rec.step_id:
                raise ValidationError(_('BMR Step is required for IPQC checks. You cannot save parameters without specifying a BMR Step.'))
            step = rec.step_id
            if not step.operator_signed_on:
                raise ValidationError(_(
                    'Cannot create an IPQC check for step "%s" — the operator '
                    'has not signed off this step yet.'
                ) % step.name)

    parameter_id = fields.Many2one(
        comodel_name='pharma.qc.spec.line',
        string='Parameter',
        required=True,
        domain="[('spec_id.product_id', '=', bmr_id.product_id), ('spec_id.stage', '=', 'ipqc')]",
        help='What is being checked, e.g. tablet hardness, weight.',
    )

    parameter = fields.Char(
        string='Parameter Name',
        related='parameter_id.parameter_name',
        store=True,
        readonly=True,
        help='Parameter name related from spec line.',
    )

    expected_min = fields.Float(
        string='Expected Min',
        help='Acceptable minimum for this in-process check.',
    )

    expected_max = fields.Float(
        string='Expected Max',
        help='Acceptable maximum for this in-process check.',
    )

    actual_value = fields.Float(
        string='Actual Value',
        help='Value recorded by the analyst.',
    )

    result = fields.Selection(
        selection=[
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ],
        string='Result',
        copy=False,
        compute='_compute_result',
        store=True,
        tracking=True,
            help='Specifies the Result for this record.',
    )

    @api.depends('actual_value', 'expected_min', 'expected_max')
    def _compute_result(self):
        """Executes the _compute_result operation."""
        for rec in self:
            if rec.actual_value:
                if rec.expected_min <= rec.actual_value <= rec.expected_max:
                    rec.result = 'pass'
                else:
                    rec.result = 'fail'
            else:
                rec.result = False

    @api.onchange('parameter_id')
    def _onchange_parameter_id(self):
        """Load the expected min and max limits from the selected parameter."""
        if self.parameter_id:
            self.expected_min = self.parameter_id.min_value
            self.expected_max = self.parameter_id.max_value
        else:
            self.expected_min = 0.0
            self.expected_max = 0.0

    @api.onchange('parameter_id', 'step_id')
    def _onchange_parameter_step(self):
        """Warn when the chosen parameter is already recorded on the same BMR step."""
        if self.step_id and self.parameter_id and self.bmr_id:
            for line in self.bmr_id.ipqc_ids:
                if line != self and line.step_id == self.step_id and line.parameter_id == self.parameter_id:
                    self.parameter_id = False
                    return {
                        'warning': {
                            'title': _("Duplicate Parameter"),
                            'message': _("The parameter '%s' is already selected for BMR step '%s'.") % (
                                line.parameter_id.parameter_name if line.parameter_id else '', self.step_id.name or ''
                            )
                        }
                    }

    @api.constrains('expected_min', 'expected_max')
    def _check_expected_range(self):
        """Expected Max must be greater than Expected Min when set."""
        for rec in self:
            # Skip checks that define no numeric range.
            if not rec.expected_min and not rec.expected_max:
                continue
            if rec.expected_max <= rec.expected_min:
                raise ValidationError(_(
                    "IPQC check '%s': Expected Max (%s) must be greater than "
                    "Expected Min (%s).",
                    rec.parameter_id.parameter_name if rec.parameter_id else _('Unnamed'),
                    rec.expected_max, rec.expected_min))

    @api.constrains('bmr_id', 'step_id', 'parameter_id')
    def _check_unique_step_parameter(self):
        """Forbid recording the same parameter twice on one BMR step."""
        for rec in self:
            if rec.bmr_id and rec.step_id and rec.parameter_id:
                duplicate = self.search([
                    ('id', '!=', rec.id),
                    ('bmr_id', '=', rec.bmr_id.id),
                    ('step_id', '=', rec.step_id.id),
                    ('parameter_id', '=', rec.parameter_id.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_(
                        "The parameter '%s' is already selected for step '%s' in this BMR."
                    ) % (rec.parameter_id.parameter_name, rec.step_id.name))

    signed_by = fields.Many2one(
        comodel_name='res.users',
        string='Signed By',
        copy=False,
        readonly=True,
            help='Specifies the Signed By for this record.',
    )

    signed_on = fields.Datetime(
        string='Signed On',
        copy=False,
        readonly=True,
            help='Specifies the Signed On for this record.',
    )

    def write(self, vals):
        """Auto-create a deviation and hold/release the BMR step on IPQC pass/fail."""
        res = super().write(vals)
        if 'result' in vals:
            for rec in self:
                if vals['result'] == 'fail':
                    # Raise a deviation for the failure — only when the optional
                    # pharma_capa_deviation module is installed (no-op otherwise).
                    rec._on_ipqc_fail()
                    # Auto-hold the linked step so execution is blocked
                    if rec.step_id and rec.step_id.status == 'pending':
                        rec.step_id._ipqc_hold()
                elif vals['result'] == 'pass':
                    # Release the IPQC-triggered hold on the step if all
                    # IPQC checks for that step are now passing
                    if rec.step_id and rec.step_id.status == 'hold':
                        step_ipqcs = rec.bmr_id.ipqc_ids.filtered(
                            lambda r: r.step_id == rec.step_id
                        )
                        if not step_ipqcs.filtered(lambda r: r.result == 'fail'):
                            rec.step_id._ipqc_release()
        return res

    def _on_ipqc_fail(self):
        """Hook to raise a deviation on IPQC failure; no-op in core."""
        return

    def action_sign(self):
        """Analyst signs the IPQC result — records who and when."""
        for rec in self:
            if rec.signed_on:
                raise UserError(_('This IPQC check is already signed.'))
            if not rec.result:
                raise UserError(_('Set the result (Pass/Fail) before signing.'))
            rec.write({
                'signed_by': self.env.user.id,
                'signed_on': fields.Datetime.now(),
            })
            if rec.result == 'fail':
                rec._on_ipqc_fail()
                if rec.step_id and rec.step_id.status == 'pending':
                    rec.step_id._ipqc_hold()
