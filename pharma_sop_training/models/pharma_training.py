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
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
        help='Specifies the Employee for this record.',
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
             'Passed = score at or above the configured passing score. '
             'Failed = score below the passing score, must retake. '
             'Expired = validity period ended, blocks regulated actions.',
    )
    assessor_id = fields.Many2one(
        comodel_name='res.users',
        string='Assessor',
        tracking=True,
        help='Person who evaluated the training and entered the score.',
    )
    score = fields.Float(
        string='Assessment Score (%)',
        digits=(5, 2),
        tracking=True,
        help='Score achieved by the employee. Compared against the configured '
             'passing score to decide Passed or Failed.',
    )
    completed_on = fields.Date(
        string='Completed On',
        copy=False,
        tracking=True,
        help='Date the employee completed the training assessment.',
    )
    expiry_date = fields.Date(
        string='Expiry Date',
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
        help='Specifies the Training for this record.',
    )
    active = fields.Boolean(
        string='Active',
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
            rec.training_name = f'{emp} / {sop}' if (sop or emp) else _('New Training')

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
                    raise ValidationError(_('An active training record already exists for this employee and SOP.'))

    @api.constrains('score')
    def _check_score_range(self):
        """Validate the assessment score is within 0 to 100."""
        for rec in self:
            if rec.score and not (0.0 <= rec.score <= 100.0):
                raise ValidationError(
                    _('Assessment score must be between 0 and 100.'))

    def action_record_assessment(self):
        """Record the assessment score and set the training Passed or Failed."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can record a training assessment.'),
        )
        passing_score = self.env.company.pharma_training_passing_score
        for rec in self:
            if rec.score is False or rec.score == 0.0:
                raise ValidationError(
                    _('Please enter the assessment score before recording the result.')
                )
            rec.write({
                'status': 'passed' if rec.score >= passing_score else 'failed',
                'assessor_id': self.env.user.id,
                'completed_on': fields.Date.today(),
            })

    def action_retake(self):
        """Archives the existing training record and creates a new active retake copy in Pending status."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can reset a training record for re-take.'),
        )
        new_trainings = self.env['pharma.training']
        for rec in self:
            old_ver = rec.version
            rec.write({'active': False})
            new_training = rec.copy({
                'active': True,
                'status': 'pending',
                'version': old_ver + 1,
                'score': 0.0,
                'completed_on': False,
                'assessor_id': False,
            })
            new_trainings |= new_training

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
            # No HR employee record linked — allow (non-GMP user)
            return True

        if not sop_ids:
            # No specific SOPs to check — clearance granted
            return True

        for sop_id in sop_ids:
            sop = self.env['pharma.sop'].browse(sop_id)
            training = self.search([
                ('employee_id', '=', employee.id),
                ('sop_id', '=', sop_id),
            ], limit=1)

            if training and (training.status == 'expired' or (training.expiry_date and training.expiry_date < fields.Date.today())):
                raise ValidationError(_("The SOP trainee's expiry date is completed."))

            if not training or training.status != 'passed':
                raise ValidationError(
                    _(
                        'Sign-off blocked: %(employee)s has no valid passed training '
                        'for SOP "%(sop)s".\n\n'
                        'Complete and pass the training before signing this step.\n'
                        '(Missing or expired training both block sign-off.)',
                        employee=employee.name,
                        sop=sop.name or str(sop_id),
                    )
                )
        return True
