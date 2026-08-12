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


class PharmaOosInvestigation(models.Model):
    """OOS Investigation — tracks investigations when QC results fall out of spec."""
    _name = 'pharma.oos.investigation'
    _description = 'OOS Investigation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Investigation Number',
        required=True,
        copy=False,
        readonly=True,
        default='/',
            help='Specifies the Investigation Number for this record.',
    )

    result_line_id = fields.Many2one(
        comodel_name='pharma.qc.result.line',
        string='OOS Result Line',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
        help='The specific OOS result that triggered this investigation.'
    )

    phase = fields.Selection(
        selection=[
            ('phase_1', 'Phase I'),
            ('phase_2', 'Phase II'),
        ],
        string='Phase',
        default='phase_1',
        required=True,
        tracking=True,
        help='Phase I checks for lab error, Phase II checks the full batch.'
    )

    lab_error_found = fields.Boolean(
        string='Lab Error Found',
        default=False,
        tracking=True,
        help='If True in Phase I, result is invalidated and re-tested.'
    )

    conclusion_notes = fields.Text(
        string='Conclusion Notes',
        tracking=True,
        help='User entered analysis and notes for the investigation.'
    )

    conclusion = fields.Text(
        string='Conclusion',
        compute='_compute_conclusion',
        inverse='_inverse_conclusion',
        tracking=True,
        help='Final conclusion of the investigation containing expected/actual values and analysis.'
    )

    @api.depends('result_line_id', 'result_line_id.parameter_id', 'result_line_id.expected_min', 'result_line_id.expected_max', 'result_line_id.actual_value', 'result_line_id.uom', 'conclusion_notes')
    def _compute_conclusion(self):
        """Build the conclusion text from the expected range, actual value and notes."""
        for rec in self:
            if rec.result_line_id:
                res_line = rec.result_line_id
                uom_str = f" {res_line.uom}" if res_line.uom else ""
                param = res_line.parameter_id.parameter_name if res_line.parameter_id else "specified parameter"
                has_min = getattr(res_line, 'has_min', True)
                has_max = getattr(res_line, 'has_max', True)
                min_val = f"{res_line.expected_min:.4f}"
                max_val = f"{res_line.expected_max:.4f}"
                act_val = f"{res_line.actual_value:.4f}"

                if has_min and has_max:
                    sentence = f"The test parameter '{param}' required for this product is expected to be between {min_val} and {max_val}{uom_str}, but the actual recorded value was {act_val}{uom_str}."
                elif has_min:
                    sentence = f"The test parameter '{param}' required for this product is expected to be at least {min_val}{uom_str}, but the actual recorded value was {act_val}{uom_str}."
                elif has_max:
                    sentence = f"The test parameter '{param}' required for this product is expected to be at most {max_val}{uom_str}, but the actual recorded value was {act_val}{uom_str}."
                else:
                    sentence = f"The test parameter '{param}' recorded an out-of-specification actual value of {act_val}{uom_str}."

                notes = rec.conclusion_notes or ""
                if notes:
                    rec.conclusion = f"{sentence}\n\nConclusion:\n{notes}"
                else:
                    rec.conclusion = sentence
            else:
                rec.conclusion = rec.conclusion_notes or ""

    def _inverse_conclusion(self):
        """Store the user-written part of an edited conclusion back into the notes."""
        for rec in self:
            val = rec.conclusion or ""
            if "Conclusion:\n" in val:
                rec.conclusion_notes = val.split("Conclusion:\n", 1)[1].strip()
            elif "The test parameter " in val and ", but the actual " in val:
                parts = val.split(", but the actual ", 1)
                if len(parts) > 1:
                    act_part = parts[1]
                    lines = act_part.splitlines()
                    if len(lines) > 1:
                        rec.conclusion_notes = "\n".join(lines[1:]).strip()
                    else:
                        rec.conclusion_notes = ""
                else:
                    rec.conclusion_notes = ""
            else:
                rec.conclusion_notes = val.strip()

    disposition = fields.Selection(
        selection=[
            ('release', 'Release'),
            ('reject', 'Reject'),
        ],
        string='Disposition',
        tracking=True,
        help='Final decision on the batch after investigation.'
    )

    investigated_by = fields.Many2one(
        comodel_name='res.users',
        string='Investigated By',
        tracking=True,
        help='QA person who led the investigation.'
    )

    closed_on = fields.Datetime(
        string='Closed On',
        tracking=True,
        help='Date and time the investigation was formally closed.'
    )

    test_order_id = fields.Many2one(
        comodel_name='pharma.qc.test.order',
        string='Test Order',
        related='result_line_id.test_order_id',
        store=True,
        help='Specifies the Test Order for this record.',
    )

    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Defected Product',
        related='result_line_id.test_order_id.product_id',
        store=True,
        readonly=True,
        help='Product associated with the OOS test order.',
    )

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot / Batch',
        related='result_line_id.test_order_id.lot_id',
        store=True,
        readonly=True,
        help='Lot / batch associated with the OOS test order.',
    )

    expected_min = fields.Float(
        string='Expected Min',
        related='result_line_id.expected_min',
        readonly=True,
        digits=(16, 4),
        help='Minimum accepted specification value.',
    )

    expected_max = fields.Float(
        string='Expected Max',
        related='result_line_id.expected_max',
        readonly=True,
        digits=(16, 4),
        help='Maximum accepted specification value.',
    )

    actual_value = fields.Float(
        string='Actual Value',
        related='result_line_id.actual_value',
        readonly=True,
        digits=(16, 4),
        help='Actual measured value that triggered the OOS.',
    )

    uom = fields.Char(
        string='UoM',
        related='result_line_id.uom',
        readonly=True,
        help='Unit of measure for the parameter.',
    )

    def action_view_test_order(self):
        """Returns a window action to open the associated QC Test Order form."""
        self.ensure_one()
        if self.test_order_id:
            return {
                'name': 'QC Test Order',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'pharma.qc.test.order',
                'res_id': self.test_order_id.id,
            }

    def action_escalate_to_phase_2(self):
        """Escalate a Phase I investigation to Phase II."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can escalate an OOS investigation.'),
        )
        for rec in self:
            if rec.closed_on:
                raise ValidationError(_("Closed investigations cannot be escalated."))
            if rec.phase != 'phase_1':
                raise ValidationError(_("Only Phase I investigations can be escalated."))
            if rec.lab_error_found:
                raise ValidationError(_("Cannot escalate to Phase II if a lab error was found. Please invalidate and re-test instead."))
            rec.phase = 'phase_2'

    def action_invalidate_retest(self):
        """Invalidate the OOS result as a lab error and permit re-testing."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can invalidate and re-test an OOS result.'),
        )
        for rec in self:
            if rec.closed_on:
                raise ValidationError(_("This investigation is already closed."))
            if rec.phase != 'phase_1':
                raise ValidationError(_("Invalidation and re-testing can only be triggered in Phase I."))
            if not rec.lab_error_found:
                raise ValidationError(_("You must select 'Lab Error Found' to invalidate and re-test."))

            # Invalidate results: reset actual_value to 0.0 and result_entered to False
            rec.result_line_id.write({
                'actual_value': 0.0,
                'result_entered': False,
            })

            # Set test order status to in_progress (if under_investigation)
            test_order = rec.result_line_id.test_order_id
            if test_order.status == 'under_investigation':
                # Check if there are other open investigations for this test order
                other_open = self.env['pharma.oos.investigation'].search([
                    ('result_line_id.test_order_id', '=', test_order.id),
                    ('id', '!=', rec.id),
                    ('closed_on', '=', False)
                ])
                if not other_open:
                    test_order.write({'status': 'in_progress'})

            rec.write({
                'investigated_by': self.env.user.id,
                'closed_on': fields.Datetime.now()
            })

    def action_close_investigation(self):
        """Close a Phase II investigation, updating the QC test order status."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can close an OOS investigation.'),
        )
        for rec in self:
            if rec.closed_on:
                raise ValidationError(_("This investigation is already closed."))
            if rec.phase != 'phase_2':
                raise ValidationError(_("Only Phase II investigations can be closed directly. "
                                        "If Phase I is sufficient, select lab error found or escalate to Phase II."))
            if not rec.conclusion:
                raise ValidationError(_("You must enter a conclusion before closing Phase II."))
            if not rec.disposition:
                raise ValidationError(_("You must enter a disposition before closing Phase II."))

            rec.write({
                'investigated_by': self.env.user.id,
                'closed_on': fields.Datetime.now()
            })

            # Create a deviation only when the batch is rejected. A "release"
            # disposition accepts the result, so no deviation is needed. The
            # deviation itself is raised by the optional pharma_capa_deviation
            # module, which overrides _create_oos_deviation(); without that
            # module installed this is a no-op (native behaviour).
            if rec.disposition == 'reject':
                rec._create_oos_deviation()

            # Update parent test order status
            test_order = rec.result_line_id.test_order_id
            if test_order:
                # If disposition is reject, set test order to failed
                if rec.disposition == 'reject':
                    test_order.write({'status': 'failed'})
                elif rec.disposition == 'release':
                    # Check if all other OOS investigations for this test order are closed
                    other_open = self.env['pharma.oos.investigation'].search([
                        ('result_line_id.test_order_id', '=', test_order.id),
                        ('id', '!=', rec.id),
                        ('closed_on', '=', False)
                    ])
                    if not other_open:
                        # Also check if any closed investigations were rejected
                        other_failed = self.env['pharma.oos.investigation'].search([
                            ('result_line_id.test_order_id', '=', test_order.id),
                            ('id', '!=', rec.id),
                            ('disposition', '=', 'reject'),
                            ('lab_error_found', '=', False)
                        ])
                        if other_failed:
                            test_order.write({'status': 'failed'})
                        else:
                            # Released with no rejected investigations: no deviation
                            # is raised, so the batch passes directly.
                            test_order.write({'status': 'passed'})

    def _create_oos_deviation(self):
        """Hook: raise a deviation for a rejected OOS investigation; no-op in core."""
        return

    @api.constrains('closed_on', 'disposition')
    def _check_close(self):
        """Require a disposition on Phase II closures."""
        for rec in self:
            if rec.closed_on and not rec.disposition:
                # Phase I lab-error closures (action_invalidate_retest) do not
                # require a disposition — only Phase II closures do.  Allow the
                # Phase I path through so that invalidate_retest can close without
                if rec.phase == 'phase_2':
                    raise ValidationError(
                        _("A Phase II investigation must have a disposition before it can be closed.")
                    )

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides creation to assign a sequential OOS investigation number."""
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('pharma.oos.investigation') or '/'
        return super().create(vals_list)

    def write(self, vals):
        """Prevent changes to restricted fields once the investigation is closed."""
        for rec in self:
            if rec.closed_on:
                restricted_fields = ('result_line_id', 'lab_error_found', 'phase', 'conclusion', 'disposition')
                if any(f in vals for f in restricted_fields):
                    raise ValidationError(_("Cannot modify details of a closed OOS investigation."))
        return super().write(vals)
