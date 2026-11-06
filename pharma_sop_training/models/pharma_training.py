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

# Set only by QA's buttons and the expiry cron. A trainee who could write them
# would clear their own sign-off gate.
_RESULT_FIELDS = frozenset({'status', 'completed_on', 'version'})
# Entered by QA only: a trainee typing them would grade their own assessment.
_ASSESSMENT_FIELDS = frozenset({'score', 'total_score'})
# Frozen once the training is passed, as in the form.
_PASSED_FIELDS = frozenset({
    'sop_id', 'employee_id', 'score', 'total_score', 'expiry_date', 'assessor_id'})


class PharmaTraining(models.Model):
    """Training record — one per employee per SOP version."""
    _name = 'pharma.training'
    _description = 'SOP Training Record'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _rec_name = 'training_name'
    _order = 'employee_id, sop_id'

    sop_id = fields.Many2one(
        comodel_name='pharma.sop',
        string='SOP',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
        help='SOP assigned for this training.',
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
        help='Employee who must complete this training.',
    )
    status = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
            ('expired', 'Expired'),
        ],
        string='Training Status',
        default='pending',
        required=True,
        tracking=True,
        index=True,
        help='Pending = not yet completed. '
             'Passed = score at or above the configured passing percentage of '
             'the Total Score. '
             'Failed = score below that threshold, must retake. '
             'Expired = validity period ended, blocks regulated actions.',
    )
    assessor_id = fields.Many2one(
        comodel_name='res.users',
        tracking=True,
        help='Person who evaluated the training and entered the score.',
    )
    total_score = fields.Float(
        aggregator='avg',
        digits=(5, 2),
        default=100.0,
        required=True,
        tracking=True,
        help='Maximum possible score for the assessment (limited to 100). Note: If '
             'the Assessment Score is below the passing score percentage configured '
             'in the Pharmaceutical ERP settings, the training is marked as Failed.',
    )
    score = fields.Float(
        string='Assessment Score',
        aggregator='avg',
        digits=(5, 2),
        tracking=True,
        help='Score achieved by the employee, out of the Total Score. Must reach '
             'the passing score percentage of the Total Score configured in the '
             'settings for the training to pass.',
    )
    completed_on = fields.Date(
        copy=False,
        tracking=True,
        help='Date the employee completed the training assessment.',
    )
    expiry_date = fields.Date(
        copy=False,
        tracking=True,
        help='Date after which this training record is considered Expired. '
             'Expired employees are blocked from signing regulated records.',
    )
    version = fields.Integer(
        string='Version / Attempt',
        default=1,
        required=True,
        readonly=True,
        tracking=True,
        help='Auto-increments each time a training record is reset for re-take.'
    )
    training_name = fields.Char(
        string='Training',
        compute='_compute_training_name',
        store=True,
        help='Employee and SOP of this training, used as its name.',
    )
    active = fields.Boolean(
        default=True,
        tracking=True,
        help='Uncheck to archive the training record.'
    )

    @api.depends('sop_id', 'employee_id')
    def _compute_training_name(self):
        """Generates a composite display name using employee name and SOP title."""
        for rec in self:
            sop = rec.sop_id.name or ''
            emp = rec.employee_id.name or ''
            rec.training_name = f'{emp} / {sop}' if (sop or emp) else self.env._('New Training')

    @api.constrains('sop_id', 'employee_id', 'active')
    def _check_unique_active_sop_employee(self):
        """Forbid more than one active training record per SOP and employee."""
        for rec in self:
            if rec.active and rec.sop_id and rec.employee_id:
                domain = [
                    ('sop_id', '=', rec.sop_id.id),
                    ('employee_id', '=', rec.employee_id.id),
                    ('active', '=', True),
                    ('id', '!=', rec.id),
                ]
                if self.search_count(domain):
                    raise ValidationError(self.env._('An active training record already exists for this employee and SOP.'))

    def write(self, vals):
        """Keep the result to QA and freeze a passed training."""
        if not self.env.su:
            if _RESULT_FIELDS & set(vals):
                raise UserError(self.env._(
                    'The result of a training is recorded by QA only.'))
            if _ASSESSMENT_FIELDS & set(vals) and not self.env.user.has_group(
                    'pharmaceutical_base.group_pharma_role_qa'):
                raise UserError(self.env._(
                    'The assessment score is entered by QA only.'))
            if _PASSED_FIELDS & set(vals) and any(
                    rec.status == 'passed' for rec in self):
                raise UserError(self.env._(
                    'A passed training cannot be changed. Reset it for a '
                    're-take instead.'))
        return super().write(vals)

    def _is_score_passing(self):
        """Return True when the assessment score meets the configured passing percentage."""
        self.ensure_one()
        if self.score <= 0.0:
            return False
        percentage = self.env.company.pharma_training_passing_score
        return self.score >= self.total_score * percentage / 100.0

    @api.constrains('score', 'total_score')
    def _check_score_validity(self):
        """Validate the assessment score against the total score."""
        for rec in self:
            if rec.total_score <= 0.0:
                raise ValidationError(
                    self.env._('You must provide a Total Score greater than 0 before saving.'))
            if rec.total_score > 100.0:
                raise ValidationError(
                    self.env._('The Total Score cannot be greater than 100.'))
            if rec.score < 0.0:
                raise ValidationError(
                    self.env._('The assessment score cannot be negative.'))
            if rec.score > rec.total_score:
                raise ValidationError(
                    self.env._('The assessment score cannot be greater than the total score.'))

    def action_record_assessment(self):
        """Record the assessment score and set the training Passed or Failed."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            self.env._('Only QA can record a training assessment.'),
        )
        for rec in self:
            if not rec.active or rec.status not in ('pending', 'failed'):
                raise UserError(self.env._(
                    'Only a pending or failed training can be assessed. Reset '
                    'it for a re-take first.'))
            if rec.score is False or rec.score == 0.0:
                raise ValidationError(
                    self.env._('Please enter the assessment score before recording the result.')
                )
            rec.sudo().write({
                'status': 'passed' if rec._is_score_passing() else 'failed',
                'assessor_id': self.env.user.id,
                'completed_on': fields.Date.today(),
            })

    def action_retake(self):
        """Archives the existing training record and creates a new active retake copy in Pending status."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            self.env._('Only QA can reset a training record for re-take.'),
        )
        new_trainings = self.env['pharma.training']
        for rec in self:
            old_ver = rec.version
            rec.write({'active': False})
            # QA has no create right on training records; the re-take copy is
            # made by the system once the QA check above has passed.
            new_training = rec.sudo().copy({
                'active': True,
                'status': 'pending',
                'version': old_ver + 1,
                'score': 0.0,
                'completed_on': False,
                'assessor_id': False,
            })
            new_trainings |= new_training.sudo(False)

        if len(new_trainings) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'pharma.training',
                'res_id': new_trainings.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.training',
            'view_mode': 'list,form',
            'domain': [('id', 'in', new_trainings.ids)],
            'target': 'current',
        }

    @api.model
    def _cron_expire_trainings(self):
        """Daily cron marking passed trainings Expired once past their expiry date."""
        today = fields.Date.today()
        expired = self.search([
            ('status', '=', 'passed'),
            ('expiry_date', '<', today),
        ])
        expired.write({'status': 'expired'})

    @api.model
    def check_training_clearance(self, user_id, sop_ids=None):
        """Raise ValidationError unless the user has passed current training for required SOPs."""
        employee = self.env['hr.employee'].search(
            [('user_id', '=', user_id)], limit=1
        )
        if not employee:
            # A user with no employee record is not GMP-tracked.
            return True

        if not sop_ids:
            return True

        for sop_id in sop_ids:
            sop = self.env['pharma.sop'].browse(sop_id)
            training = self.search([
                ('employee_id', '=', employee.id),
                ('sop_id', '=', sop_id),
            ], limit=1)

            if training and (training.status == 'expired' or (training.expiry_date and training.expiry_date < fields.Date.today())):
                raise ValidationError(self.env._(
                    'Sign-off blocked: the training of %(employee)s for SOP "%(sop)s" '
                    'has expired. Complete the training again before signing this step.',
                    employee=employee.name, sop=sop.name or str(sop_id)))

            if not training or training.status != 'passed':
                raise ValidationError(
                    self.env._(
                        'Sign-off blocked: %(employee)s has no valid passed training '
                        'for SOP "%(sop)s".\n\n'
                        'Complete and pass the training before signing this step.\n'
                        '(Missing or expired training both block sign-off.)',
                        employee=employee.name,
                        sop=sop.name or str(sop_id),
                    )
                )
        return True
