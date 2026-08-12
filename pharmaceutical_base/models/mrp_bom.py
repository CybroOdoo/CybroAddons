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


class MrpBom(models.Model):
    """Extends the BoM (Formula) with versioning, pharmacopoeial reference, and QA approval."""
    _inherit = ['mrp.bom', 'pharma.workflow.mixin']

    @api.model_create_multi
    def create(self, vals_list):
        """Executes the create operation."""
        records = super().create(vals_list)
        records._merge_identical_lines()
        return records

    def write(self, vals):
        """Executes the write operation."""
        res = super().write(vals)
        if 'bom_line_ids' in vals:
            self._merge_identical_lines()
        return res

    def _merge_identical_lines(self):
        """Merges identical product lines into a single line with summed quantities."""
        for bom in self:
            seen = {}
            lines_to_unlink = self.env['mrp.bom.line']
            for line in bom.bom_line_ids:
                if not line.product_id:
                    continue
                key = (line.product_id.id, line.product_uom_id.id)
                if key in seen:
                    seen[key].product_qty += line.product_qty
                    lines_to_unlink |= line
                else:
                    seen[key] = line
            if lines_to_unlink:
                lines_to_unlink.unlink()

    # ── Pharma Formula Fields ─────────────────────────────────────────────────
    formula_version = fields.Integer(
        string='BOM Version',
        default=1,
        copy=False,
        tracking=True,
        help='Version identifier for this formula. '
             'Increments automatically when reset to draft.',
    )

    formula_status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('obsolete', 'Obsolete'),
        ],
        string='Formula Status',
        default='draft',
        required=True,
        tracking=True,
        help='Only Approved formulas can be used to start a production order.',
    )

    pharmacopoeial_ref = fields.Selection(
        selection=[
            ('bp', 'BP (British Pharmacopoeia)'),
            ('usp', 'USP (United States Pharmacopeia)'),
            ('ep', 'EP (European Pharmacopoeia)'),
            ('ip', 'IP (Indian Pharmacopoeia)'),
            ('inhouse', 'In-House Specification'),
        ],
        string='Pharmacopoeial Reference',
        tracking=True,
        help='Standard this formula is written against.',
    )

    # ── Approval Fields ───────────────────────────────────────────────────────
    approved_by = fields.Many2one(
        comodel_name='res.users',
        string='Approved By',
        copy=False,
        tracking=True,
        help='QA person who signed off on this formula.',
    )

    approval_date = fields.Date(
        string='Approval Date',
        copy=False,
        tracking=True,
        help='Date the formula was approved for production use.',
    )

    # ── Theoretical Yield ────────────────────────────────────────────────────
    theoretical_yield = fields.Float(
        string='Theoretical Yield (%)',
        digits=(5, 2),
        default=100.0,
        tracking=True,
        help='Expected batch yield percentage. Values below the configured '
             'threshold trigger a QA investigation.',
    )

    # ── Change Control Reference ──────────────────────────────────────────────
    change_ref = fields.Char(
        string='Change Control Ref.',
        copy=False,
        tracking=True,
        help='Reference to the Change Control record that authorised this formula version.',
    )

    notes = fields.Text(help='Specifies the Notes for this record.', string='Formula Notes / Manufacturing Instructions')

    # ── Constraints ───────────────────────────────────────────────────────────
    @api.constrains('formula_status', 'approved_by', 'approval_date')
    def _check_approval_fields(self):
        """Require an approver and approval date when a formula is approved."""
        for rec in self:
            if rec.formula_status in ('approved', 'done') and not (rec.approved_by and rec.approval_date):
                raise ValidationError(
                    _('Approved By and Approval Date are required when setting formula status to Approved.')
                )

    @api.constrains('operation_ids', 'formula_status')
    def _check_operations_required(self):
        """Ensure an approved BOM has at least one operation defined."""
        for rec in self:
            if rec.formula_status in ('approved', 'done'):
                if not rec.operation_ids:
                    raise ValidationError(_("A Pharma Formula (BOM) must have at least one Operation (Work Center) defined before it can be approved."))

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_approve_formula(self):
        """Approves the formula for production use, recording the current user and date."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can approve a manufacturing formula.'),
        )
        for rec in self:
            rec.write({
                'formula_status': 'approved',
                'approved_by': self.env.user.id,
                'approval_date': fields.Date.today(),
            })

    def action_obsolete_formula(self):
        """Marks the formula as obsolete, preventing its use in future production orders."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can mark a manufacturing formula obsolete.'),
        )
        self.write({'formula_status': 'obsolete'})

    def action_reset_draft(self):
        """Revert the formula to Draft, increment the version, and clear approvals."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can reset a manufacturing formula to draft.'),
        )
        for rec in self:
            rec.write({
                'formula_status': 'draft',
                'formula_version': rec.formula_version + 1,
                'approved_by': False,
                'approval_date': False,
            })
