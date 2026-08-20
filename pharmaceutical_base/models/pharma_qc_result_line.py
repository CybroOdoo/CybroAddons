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
from odoo.tools.translate import _


class PharmaQcResultLine(models.Model):
    """QC Result Line — records the actual testing values for each parameter."""
    _name = 'pharma.qc.result.line'
    _description = 'QC Result Line'
    _rec_name = 'parameter_id'

    test_order_id = fields.Many2one(
        comodel_name='pharma.qc.test.order',
        string='Test Order',
        required=True,
        ondelete='cascade',
        index=True,
        help='Specifies the Test Order for this record.',
    )
    test_stage = fields.Selection(help='Specifies the Test Stage for this record.',
        related='test_order_id.stage',
        string='Stage',
        readonly=True,
    )
    test_status = fields.Selection(help='Specifies the Test Status for this record.',
        related='test_order_id.status',
        string='Test Status',
        readonly=True,
    )
    parameter_id = fields.Many2one(
        comodel_name='pharma.qc.spec.line',
        string='Parameter',
        domain="[('spec_id.product_id', '=', test_order_id.product_id)]",
        help='Test parameter from spec.'
    )
    parameter = fields.Char(
        string='Parameter Name',
        related='parameter_id.parameter_name',
        store=True,
        readonly=True,
        help='Parameter name related from parameter spec line.'
    )
    expected_min = fields.Float(
        string='Expected Min',
        digits=(16, 4),
        help='Minimum copied from spec for reference during entry.',
        store=True
    )
    has_min = fields.Boolean(
        string='Has Min Limit',
        default=True,
        help='When True the expected_min is enforced, even if it is 0.0. '
             'Set to False for parameters that have no lower bound.'
    )
    expected_max = fields.Float(
        string='Expected Max',
        digits=(16, 4),
        help='Maximum copied from spec for reference during entry.',
        store=True
    )
    has_max = fields.Boolean(
        string='Has Max Limit',
        default=True,
        help='When True the expected_max is enforced, even if it is 0.0. '
             'Set to False for parameters that have no upper bound.'
    )
    actual_value = fields.Float(
        string='Actual Value',
        digits=(16, 4),
        help='Result entered by the analyst after running the test.'
    )
    uom = fields.Char(
        string='UoM',
        help='Unit of measurement for this result.'
    )
    result_entered = fields.Boolean(
        string='Result Entered',
        default=False,
        help='Indicates if the actual test result has been entered.'
    )
    is_oos = fields.Boolean(
        string='OOS',
        compute='_compute_status',
        store=True,
        help='Auto set to True if actual value falls outside min/max.'
    )
    status = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('pass', 'Pass'),
            ('oos', 'OOS'),
        ],
        string='Result Status',
        compute='_compute_status',
        store=True,
        help='Pending — result not entered yet. Pass — value within the accepted min/max range. OOS — value entered and outside the accepted limits.',
        default='pending',
    )

    @api.depends(
        'actual_value', 'expected_min', 'has_min',
        'expected_max', 'has_max', 'result_entered',
    )
    def _compute_status(self):
        """Flag the result OOS by comparing the value to its limits."""
        for rec in self:
            is_oos = False
            if rec.result_entered:
                if rec.has_min and rec.actual_value < rec.expected_min:
                    is_oos = True
                if rec.has_max and rec.actual_value > rec.expected_max:
                    is_oos = True
                rec.is_oos = is_oos
                rec.status = 'oos' if is_oos else 'pass'
            else:
                rec.is_oos = False
                rec.status = 'pending'

    @api.onchange('parameter_id')
    def _onchange_parameter_id(self):
        """Load the expected min and max limits from the selected specification parameter."""
        if self.parameter_id:
            self.expected_min = self.parameter_id.min_value
            self.expected_max = self.parameter_id.max_value
            self.uom = self.parameter_id.uom_id.name or ''
            self.has_min = self.parameter_id.min_value != 0.0
            self.has_max = self.parameter_id.max_value != 0.0
        else:
            self.expected_min = 0.0
            self.expected_max = 0.0
            self.uom = ''
            self.has_min = False
            self.has_max = False

    @api.onchange('actual_value')
    def _onchange_actual_value(self):
        """Mark the result entered once an actual value is recorded."""
        self.result_entered = True

    @api.model_create_multi
    def create(self, vals_list):
        """Flag entered results and auto-trigger OOS when limits are exceeded."""
        for vals in vals_list:
            if 'actual_value' in vals:
                _is_zero_spec = (
                    vals.get('actual_value') == 0.0
                    and vals.get('expected_min', 0.0) == 0.0
                    and vals.get('expected_max', 0.0) == 0.0
                )
                if vals.get('actual_value') != 0.0 or _is_zero_spec:
                    vals['result_entered'] = True
        records = super().create(vals_list)
        for rec in records:
            if rec.is_oos:
                rec._create_oos_investigation()
        return records

    def write(self, vals):
        """Allow editing results only while In Progress or Under Investigation; auto-trigger OOS on breach."""
        if 'actual_value' in vals and 'result_entered' not in vals:
            if vals.get('actual_value') != 0.0:
                vals['result_entered'] = True

        _is_invalidation_reset = (
            vals.get('actual_value') == 0.0
            and vals.get('result_entered') is False
        )
        if 'actual_value' in vals and not _is_invalidation_reset:
            for rec in self:
                is_entered = vals.get('result_entered', rec.result_entered)
                if is_entered and rec.test_order_id and rec.test_order_id.status not in ('in_progress', 'under_investigation'):
                    raise ValidationError(
                        _('Results can only be entered once the test has been started '
                          '(test order In Progress).')
                    )
        pre_oos = {rec.id: rec.is_oos for rec in self}
        res = super().write(vals)
        for rec in self:
            if rec.is_oos and not pre_oos.get(rec.id):
                existing = self.env['pharma.oos.investigation'].search([
                    ('result_line_id', '=', rec.id),
                    ('closed_on', '=', False)
                ], limit=1)
                if not existing:
                    rec._create_oos_investigation()
        return res

    def _create_oos_investigation(self):
        """Create oos investigation."""
        self.ensure_one()
        self.env['pharma.oos.investigation'].create({
            'result_line_id': self.id,
            'phase': 'phase_1',
        })

        if self.test_order_id and self.test_order_id.status != 'under_investigation':
            self.test_order_id.write({'status': 'under_investigation'})
