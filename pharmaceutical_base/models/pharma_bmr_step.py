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
from odoo.exceptions import UserError
from odoo.tools.translate import _

class PharmaBMRStep(models.Model):
    """A single execution step within a Batch Manufacturing Record."""
    _name = 'pharma.bmr.step'
    _description = 'BMR Execution Step'
    _inherit = ['mail.thread', 'pharma.workflow.mixin']
    _order = 'bmr_id, sequence, id'

    name = fields.Char(
        string='Step',
        compute='_compute_name',
        store=True,
        help='Specifies the Step for this record.',
    )
    bmr_id = fields.Many2one(
        comodel_name='pharma.bmr',
        string='BMR',
        required=True,
        ondelete='cascade',
        index=True,
        help='Specifies the BMR for this record.',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Specifies the Sequence for this record.',
    )
    description = fields.Text(
        string='Step Description',
        required=True,
        help='Specifies the Step Description for this record.',
    )
    status = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('done', 'Done'),
            ('hold', 'Hold'),
        ],
        string='Status',
        default='pending',
        required=True,
        help='Specifies the Status for this record.',
    )
    hold_source_step_id = fields.Many2one(
        comodel_name='pharma.bmr.step',
        string='Hold Source Step',
        copy=False,
        readonly=True,
        ondelete='set null',
        help='Set when this step is on hold because an earlier step was put on hold.',
    )
    operator_id = fields.Many2one(
        comodel_name='res.users',
        string='Operator',
        copy=False,
        help='Specifies the Operator for this record.',
    )
    operator_signed_on = fields.Datetime(
        string='Operator Signed On',
        copy=False,
        readonly=True,
        help='Specifies the Operator Signed On for this record.',
    )
    supervisor_id = fields.Many2one(
        comodel_name='res.users',
        string='Supervisor',
        copy=False,
        help='Specifies the Supervisor for this record.',
    )
    supervisor_signed_on = fields.Datetime(
        string='Supervisor Signed On',
        copy=False,
        readonly=True,
        help='Specifies the Supervisor Signed On for this record.',
    )

    @api.depends('sequence', 'description')
    def _compute_name(self):
        """Build the step display name from its sequence and description."""
        for step in self:
            description = (step.description or '').strip()
            step.name = '%s - %s' % (step.sequence, description) if description else _('Step %s') % step.sequence

    @api.constrains('operator_id', 'supervisor_id')
    def _check_different_users(self):
        """Validates that the operator and supervisor sign-offs are performed by different users."""
        for step in self:
            if step.operator_id and step.supervisor_id and \
                    step.operator_id == step.supervisor_id:
                continue

    def action_operator_sign(self):
        """Operator signs the step, recording who executed it and when."""
        for step in self:
            if step.status != 'pending':
                raise UserError(_('Only Pending steps can receive an operator sign-off.'))
            if step.operator_signed_on:
                raise UserError(_('This step already has an operator sign-off.'))

            held_step = step.bmr_id.step_ids.filtered(lambda s: s.status == 'hold' and s.sequence <= step.sequence)
            if held_step:
                raise UserError(_('Cannot sign this step — Step %s is currently on Hold. Release it before proceeding.') % held_step[0].sequence)

            step.write({
                'operator_id': self.env.user.id,
                'operator_signed_on': fields.Datetime.now(),
            })
            step.bmr_id.message_post(
                body=_('Step "%s" operator sign-off by %s.') % (
                    step.description[:60], self.env.user.name
                )
            )

    def action_supervisor_sign(self):
        """Supervisor independently verifies the step and marks it Done."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can give a supervisor sign-off on a BMR step.'),
        )
        for step in self:
            if step.status != 'pending':
                raise UserError(_('Only Pending steps can receive a supervisor sign-off.'))
            if not step.operator_signed_on:
                raise UserError(_('The operator must sign off before the supervisor.'))
            if step.supervisor_signed_on:
                raise UserError(_('This step already has a supervisor sign-off.'))

            ipqcs = step.bmr_id.ipqc_ids.filtered(lambda r: r.step_id == step)
            if any(not r.signed_on for r in ipqcs):
                raise UserError(_('Complete and sign all IPQC checks for this step before supervisor sign-off.'))

            # Block sign-off while the batch has open Deviations / CAPAs. This
            # gate lives in the optional pharma_capa_deviation module (no-op
            # here when that module is not installed).
            step._check_open_deviations_capas()
            step.write({
                'supervisor_id': self.env.user.id,
                'supervisor_signed_on': fields.Datetime.now(),
                'status': 'done',
            })
            step.bmr_id.message_post(
                body=_('Step "%s" completed. Supervisor sign-off by %s.') % (
                    step.description[:60], self.env.user.name
                )
            )

    def _check_open_deviations_capas(self):
        """Hook to block supervisor sign-off on open deviations/CAPAs; no-op in core."""
        return

    def action_hold(self):
        """Put this step on Hold and cascade Hold to subsequent Pending steps."""
        for step in self:
            if step.status == 'done':
                raise UserError(_('Completed steps cannot be placed on hold.'))
            if step.status == 'hold':
                raise UserError(_('Step is already on hold.'))
            step.write({
                'status': 'hold',
                'hold_source_step_id': False,
            })

            cascaded_steps = step.bmr_id.step_ids.filtered(
                lambda s: s.status == 'pending' and s.sequence > step.sequence
            )
            cascaded_steps.write({
                'status': 'hold',
                'hold_source_step_id': step.id,
            })

            bmr = step.bmr_id
            if bmr.status == 'in_progress':
                bmr.status = 'on_hold'
                bmr.message_post(
                    body=_('BMR placed on hold — step "%s" put on hold by %s.') % (
                        step.description[:60], self.env.user.name
                    )
                )
            if cascaded_steps:
                bmr.message_post(
                    body=_(
                        'Hold cascaded from step "%(step)s" to pending subsequent step(s): %(steps)s.'
                    ) % {
                        'step': step.description[:60],
                        'steps': ', '.join(cascaded_steps.mapped('name')),
                    }
                )

    def action_release_hold(self):
        """Release the directly held step and restore its cascaded holds."""
        for step in self:
            if step.status != 'hold':
                raise UserError(_('Only steps on Hold can be released.'))
            if step.hold_source_step_id:
                raise UserError(_(
                    'This step is on hold because step "%s" is on hold. '
                    'Release the source step first.'
                ) % step.hold_source_step_id.name)

            cascaded_steps = step.bmr_id.step_ids.filtered(
                lambda s: s.status == 'hold' and s.hold_source_step_id == step
            )
            (step | cascaded_steps).write({
                'status': 'pending',
                'hold_source_step_id': False,
            })
            step.bmr_id.message_post(
                body=_('Step "%s" released from hold by %s.') % (
                    step.description[:60], self.env.user.name
                )
            )
            if cascaded_steps:
                step.bmr_id.message_post(
                    body=_(
                        'Cascaded hold released. Step(s) restored to Pending: %s.'
                    ) % ', '.join(cascaded_steps.mapped('name'))
                )

    def _ipqc_hold(self):
        """Hold this step on IPQC failure and cascade to later steps."""
        for step in self:
            if step.status in ('done', 'hold'):
                continue
            step.write({'status': 'hold', 'hold_source_step_id': False})
            cascaded = step.bmr_id.step_ids.filtered(
                lambda s: s.status == 'pending' and s.sequence > step.sequence
            )
            cascaded.write({'status': 'hold', 'hold_source_step_id': step.id})
            bmr = step.bmr_id
            if bmr.status == 'in_progress':
                bmr.status = 'on_hold'
                bmr.message_post(body=_(
                    'BMR placed on Hold — IPQC check failed on step "%s". '
                    'Resolve the failure before resuming.'
                ) % step.description[:60])

    def _ipqc_release(self):
        """Release the IPQC hold once all IPQC checks for the step pass."""
        for step in self:
            if step.status != 'hold':
                continue
            cascaded = step.bmr_id.step_ids.filtered(
                lambda s: s.status == 'hold' and s.hold_source_step_id == step
            )
            (step | cascaded).write({'status': 'pending', 'hold_source_step_id': False})
            bmr = step.bmr_id
            # Only resume BMR if no other steps are still on hold
            if bmr.status == 'on_hold' and not bmr.step_ids.filtered(lambda s: s.status == 'hold'):
                bmr.status = 'in_progress'
                bmr.message_post(body=_(
                    'BMR resumed — IPQC checks for step "%s" cleared. '
                    'Step and subsequent steps restored to Pending.'
                ) % step.description[:60])
