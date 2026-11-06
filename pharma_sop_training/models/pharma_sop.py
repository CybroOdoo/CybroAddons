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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# Set only by the workflow buttons, which write them elevated once their own
# checks have passed. Written directly they would let a User approve an SOP.
_WORKFLOW_FIELDS = frozenset({
    'status', 'approved_by', 'effective_date', 'version', 'sop_code'})
# Frozen once the SOP is Effective or archived, as in the form.
_CONTENT_FIELDS = frozenset({
    'name', 'workcenter_id', 'author_id', 'reviewer_id', 'review_due_date',
    'document', 'filename', 'employee_ids', 'notes'})


class PharmaSop(models.Model):
    """Standard Operating Procedure; generates training records when it becomes Effective."""
    _name = 'pharma.sop'
    _description = 'Standard Operating Procedure'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin', 'hr.mixin']
    _order = 'sop_code desc'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='SOP Title',
        required=True,
        tracking=True,
        help='Descriptive title of this Standard Operating Procedure.',
    )
    sop_code = fields.Char(
        string='SOP Code',
        copy=False,
        readonly=True,
        tracking=True,
        default=lambda self: self.env._('New'),
        help='Auto-generated unique SOP reference code (e.g. SOP/0001).',
    )
    workcenter_id = fields.Many2one(
        comodel_name='mrp.workcenter',
        string='Work Center',
        required=True,
        tracking=True,
        help='Work Center associated with this SOP. Used to filter SOPs on BOM operations.',
    )
    active = fields.Boolean(
        default=True,
        tracking=True,
        help='Uncheck to archive the SOP record.'
    )
    version = fields.Integer(
        default=1,
        required=True,
        copy=False,
        tracking=True,
        help='Auto-increments each time an archived SOP is revised and approved again.',
    )
    # ── Document ──────────────────────────────────────────────────────────────
    document = fields.Binary(
        string='SOP Document',
        attachment=True,
        help='Upload the SOP file (PDF, DOCX, etc.).',
    )
    filename = fields.Char(
        help='Original filename of the uploaded SOP document.',
    )
    # ── Workflow State ────────────────────────────────────────────────────────
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('review', 'Under Review'),
            ('effective', 'Effective'),
            ('archived', 'Archived'),
        ],
        default='draft',
        required=True,
        tracking=True,
        help='Workflow state of this SOP. Only Effective SOPs can be linked to BMR steps.',
    )
    # ── People ────────────────────────────────────────────────────────────────
    author_id = fields.Many2one(
        comodel_name='res.users',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help='Creator of this SOP. The author cannot approve their own SOP.',
    )
    reviewer_id = fields.Many2one(
        comodel_name='res.users',
        tracking=True,
        help='User who reviewed the SOP before it was submitted for QA approval.',
    )
    approved_by = fields.Many2one(
        comodel_name='res.users',
        copy=False,
        tracking=True,
        help='QA approver. Must be a different user from the author.',
    )
    # ── Dates ─────────────────────────────────────────────────────────────────
    effective_date = fields.Date(
        copy=False,
        tracking=True,
        help='Date from which this SOP version is active and usable.',
    )
    review_due_date = fields.Date(
        tracking=True,
        help='Periodic review date — the SOP should be re-evaluated before this date.',
    )
    # ── Assigned Employees ────────────────────────────────────────────────────
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='pharma_sop_employee_rel',
        column1='sop_id',
        column2='employee_id',
        string='Assigned Employees',
        help='Employees who must be trained on this SOP. '
             'When the SOP reaches Effective status, one training record '
             'is created for each employee listed here.',
    )
    employee_count = fields.Integer(
        string='Assigned Employees Count',
        compute='_compute_employee_count',
        help='Number of employees assigned to this SOP.',
    )
    # ── Training Records ──────────────────────────────────────────────────────
    training_ids = fields.One2many(
        comodel_name='pharma.training',
        inverse_name='sop_id',
        string='Training Records',
        help='Auto-generated training records for assigned employees.',
    )
    training_count = fields.Integer(
        compute='_compute_training_count',
        help='Number of training records of this SOP, archived ones included.',
    )
    notes = fields.Text(
        help='Additional remarks, change history summary, or cross-references.',
    )

    # ── Computes ──────────────────────────────────────────────────────────────
    @api.depends('name', 'sop_code')
    def _compute_display_name(self):
        """Displays descriptive title along with SOP code in selectors."""
        for rec in self:
            if rec.sop_code and rec.sop_code != self.env._('New'):
                rec.display_name = f"[{rec.sop_code}] {rec.name}"
            else:
                rec.display_name = rec.name

    @api.depends('employee_ids')
    def _compute_employee_count(self):
        """Calculates the total number of employees assigned to this SOP."""
        for rec in self:
            rec.employee_count = len(rec.employee_ids)

    @api.depends('training_ids')
    def _compute_training_count(self):
        """Calculates the total number of training records associated with this SOP (including archived)."""
        for rec in self:
            rec.training_count = self.env['pharma.training'].with_context(active_test=False).search_count([('sop_id', '=', rec.id)])

    @api.model_create_multi
    def create(self, vals_list):
        """Assign a sequential SOP Code from ir.sequence on creation."""
        for vals in vals_list:
            if not self.env.su and (
                    vals.get('status', 'draft') != 'draft'
                    or vals.get('approved_by') or vals.get('effective_date')
                    or vals.get('sop_code', self.env._('New')) != self.env._('New')):
                raise UserError(self.env._(
                    'A new SOP starts as a numbered Draft; QA makes it Effective.'))
            if vals.get('sop_code', self.env._('New')) == self.env._('New'):
                vals['sop_code'] = self.env['ir.sequence'].next_by_code(
                    'pharma.sop.sequence'
                ) or self.env._('New')
        return super().create(vals_list)

    def write(self, vals):
        """Keep the approval to the workflow and freeze an approved SOP."""
        if not self.env.su:
            if _WORKFLOW_FIELDS & set(vals):
                raise UserError(self.env._(
                    'The status, approval and version of an SOP are set by its '
                    'workflow buttons only.'))
            if _CONTENT_FIELDS & set(vals) and any(
                    not rec.active or rec.status in ('effective', 'archived')
                    for rec in self):
                raise UserError(self.env._(
                    'An Effective or archived SOP cannot be edited. Revise it '
                    'to start a new version.'))
        return super().write(vals)

    @api.constrains('sop_code')
    def _check_sop_code_unique(self):
        """Guarantee the SOP Code is a unique serial reference for active SOPs."""
        for rec in self:
            if not rec.sop_code or rec.sop_code == self.env._('New'):
                continue
            duplicate = self.search_count([
                ('sop_code', '=', rec.sop_code),
                ('id', '!=', rec.id),
                ('active', '=', True),
            ])
            if duplicate:
                raise ValidationError(self.env._(
                    "The SOP Code '%s' already exists. It must be unique.",
                    rec.sop_code))

    # ── Constraints ───────────────────────────────────────────────────────────
    @api.constrains('employee_ids')
    def _check_employee_ids(self):
        """An SOP must name at least one employee to train."""
        for rec in self:
            if not rec.employee_ids:
                raise ValidationError(self.env._("Assigned Employees is a required field. You must assign at least one employee to the SOP."))

    @api.constrains('status', 'approved_by', 'effective_date')
    def _check_effective_fields(self):
        """Require an approver and effective date when marking the SOP Effective."""
        for rec in self:
            if rec.status == 'effective' and not (
                    rec.approved_by and rec.effective_date):
                raise ValidationError(
                    self.env._('Approved By and Effective Date are required when '
                      'setting the SOP status to Effective.')
                )

    @api.constrains('author_id', 'approved_by')
    def _check_approver_not_author(self):
        """The author of an SOP cannot approve it."""
        for rec in self:
            if rec.approved_by and rec.approved_by == rec.author_id:
                raise ValidationError(self.env._(
                    'The author of an SOP cannot approve it. Ask another QA reviewer.'))

    # ── Workflow Actions ──────────────────────────────────────────────────────
    def action_submit_review(self):
        """Move the SOP to Under Review for QA approval."""
        self.check_access('write')
        if any(not rec.active or rec.status != 'draft' for rec in self):
            raise UserError(self.env._('Only a Draft SOP can be submitted for review.'))
        self.sudo().write({'status': 'review'})

    def action_approve(self):
        """QA approver marks the SOP Effective and generates training records."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            self.env._('Only QA can approve an SOP and make it effective.'),
        )
        for rec in self:
            if not rec.active or rec.status != 'review':
                raise UserError(self.env._(
                    'Only an SOP Under Review can be approved.'))
            vals = {
                'status': 'effective',
                'approved_by': self.env.user.id,
            }
            if not rec.effective_date:
                vals['effective_date'] = fields.Date.today()
            rec.sudo().write(vals)
            rec._generate_training_records()

    def action_archive_sop(self):
        """Changes the SOP status to 'Archived', indicating it is no longer active."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            self.env._('Only QA can archive an SOP.'),
        )
        self.sudo().write({'status': 'archived', 'active': False})

    def action_revise(self):
        """Start a new revision cycle from an SOP, archiving the old record and its training records, and creating a new draft copy."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            self.env._('Only QA can revise an SOP.'),
        )
        new_sops = self.env['pharma.sop']
        for rec in self:
            old_ver = rec.version
            rec.sudo().write({
                'active': False,
                'status': 'archived',
            })
            old_trainings = self.env['pharma.training'].search([
                ('sop_id', '=', rec.id),
                ('active', '=', True),
            ])
            old_trainings.write({'active': False})

            # QA has no create right on SOPs: the new draft revision is made
            # elevated once the QA check above has passed.
            new_sop = rec.sudo().copy({
                'name': rec.name,
                'sop_code': rec.sop_code,
                'active': True,
                'status': 'draft',
                'version': old_ver + 1,
                'approved_by': False,
                'effective_date': False,
                # Read elevated: users without HR rights cannot copy the employees.
                'employee_ids': [(6, 0, rec.sudo().employee_ids.ids)],
            })
            new_sops |= new_sop.sudo(False)

        if len(new_sops) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'pharma.sop',
                'res_id': new_sops.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.sop',
            'view_mode': 'list,form',
            'domain': [('id', 'in', new_sops.ids)],
            'target': 'current',
        }

    def action_reset_draft(self):
        """Archives the current SOP and creates a new revision copy in Draft."""
        return self.action_revise()

    def _generate_training_records(self):
        """Create a training record per applicable employee when the SOP becomes Effective."""
        Training = self.env['pharma.training']
        for sop in self:
            if not sop.sudo().employee_ids:
                continue

            if sop.sop_code:
                prior_sops = self.env['pharma.sop'].with_context(active_test=False).search([
                    ('sop_code', '=', sop.sop_code),
                    ('id', '!=', sop.id),
                ])
                if prior_sops:
                    prior_trainings = Training.with_context(active_test=False).search([
                        ('sop_id', 'in', prior_sops.ids),
                        ('active', '=', True),
                    ])
                    prior_trainings.write({'active': False})

            # Read elevated: QA approves the SOP without HR rights, and would
            # otherwise see no employees and generate no training records.
            for employee in sop.sudo().employee_ids:
                existing = Training.search([
                    ('sop_id', '=', sop.id),
                    ('employee_id', '=', employee.id),
                ], limit=1)
                if not existing:
                    # Training records are auto-generated when QA approves the
                    # SOP; QA has no create right, so they are created elevated.
                    Training.sudo().create({
                        'sop_id': sop.id,
                        'employee_id': employee.id,
                        'status': 'pending',
                        'active': True,
                    })

    def action_view_trainings(self):
        """Open all training records related to this SOP (including archived ones)."""
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Training Records'),
            'res_model': 'pharma.training',
            'view_mode': 'list,form',
            'domain': [('sop_id', '=', self.id)],
            'context': {'default_sop_id': self.id, 'active_test': False},
        }
