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

# Kanban column each pharma state is shown in. The pharma state is
# authoritative; the stage only mirrors it.
STAGE_BY_STATE = {
    'new': 'maintenance.stage_0',
    'in_progress': 'maintenance.stage_1',
    'completed': 'pharma_equipment_maintenance.stage_pharma_completed',
    'qa_verified': 'pharma_equipment_maintenance.stage_pharma_qa_verified',
}


class MaintenanceRequest(models.Model):
    """Maintenance activity under GMP: engineering completes, QA releases.

    Three kinds are recorded: preventive, breakdown (corrective) and
    cleaning. Each moves New -> In Progress -> Completed -> QA Verified.
    Verification is restricted to QA and links the verified cleaning to the
    equipment, so recorded dates cannot drift from what was done.
    Calibrations are not maintenance requests: they run on their own record.
    """
    _name = 'maintenance.request'
    _inherit = ['maintenance.request', 'pharma.workflow.mixin']

    maintenance_type = fields.Selection(
        selection_add=[('cleaning', 'Cleaning')],
        ondelete={'cleaning': 'set default'},
    )
    pharma_state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('qa_verified', 'QA Verified'),
        ],
        string='GMP Status',
        default='new',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        help='New, In Progress, Completed by engineering, then QA Verified: '
             'only then is the equipment released back to GMP use.',
    )
    equipment_class = fields.Selection(
        related='equipment_id.equipment_class', string='Equipment Class')
    gmp_critical = fields.Boolean(
        related='equipment_id.gmp_critical', string='GMP Critical')
    completed_by = fields.Many2one(
        comodel_name='res.users', readonly=True,
        copy=False, tracking=True,
        help='Who marked the work completed.')
    completed_on = fields.Datetime(
        readonly=True, copy=False, tracking=True,
        help='When the work was marked completed.')
    qa_verified_by = fields.Many2one(
        comodel_name='res.users', string='QA Verified By', readonly=True,
        copy=False, tracking=True,
        help='QA reviewer who released the equipment back to use.')
    qa_verified_on = fields.Datetime(
        string='QA Verified On', readonly=True, copy=False, tracking=True,
        help='When QA released the equipment back to use.')
    work_done = fields.Text(
        string='Work Performed',
        copy=False,
        help='What was done. Required to complete the request.',
    )
    requalification_required = fields.Boolean(
        copy=False,
        tracking=True,
        help='The repair or change affects the qualified state. On QA '
             'verification the equipment becomes due for requalification.',
    )

    # ---- Cleaning ---------------------------------------------------------
    clean_hold_hours = fields.Integer(
        string='Clean Hold (Hours)', compute='_compute_cleaning_settings',
        store=True, readonly=False, copy=False, tracking=True,
        help='After cleaning: how many hours the equipment can wait unused '
             'and still count as clean. After that it must be cleaned again '
             'before use. 0 means no limit. Copied from the last cleaning.')
    dirty_hold_hours = fields.Integer(
        string='Dirty Hold (Hours)', compute='_compute_cleaning_settings',
        store=True, readonly=False, copy=False, tracking=True,
        help='After use: how many hours the equipment can wait dirty before '
             'cleaning must start. A cleaning started later is marked for QA '
             'to check. 0 means no limit. Copied from the last cleaning.')
    dirty_hold_exceeded = fields.Boolean(
        readonly=True, copy=False, tracking=True,
        help='This cleaning started too late: the equipment was left dirty '
             'longer than its dirty hold. QA should check the cleaning worked.')

    # ---- Sterilisation (sterile sites, cleaning requests) ----------------
    sterilisation_method = fields.Selection(
        selection=[
            ('steam', 'Steam (Autoclave)'),
            ('dry_heat', 'Dry Heat'),
            ('chemical', 'Chemical'),
            ('radiation', 'Radiation'),
        ],
        compute='_compute_sterilisation_settings',
        store=True, readonly=False, copy=False,
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='Validated sterilisation method used. Taken from the previous '
             'sterilisation of the equipment.')
    sterile_hold_hours = fields.Integer(
        string='Sterile Hold (Hours)', compute='_compute_sterilisation_settings',
        store=True, readonly=False, copy=False,
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='How long the equipment stays sterile after this cycle. Zero '
             'means the sterile state does not expire.')
    # No field groups: the equipment's Sterilisation Records list filters on
    # it, which every user creating a cleaning goes through. Views hide it.
    sterilisation_performed = fields.Boolean(
        string='Sterilised After Cleaning',
        copy=False,
        help='A sterilisation cycle followed the cleaning.',
    )
    sterilisation_cycle_ref = fields.Char(
        string='Sterilisation Cycle',
        copy=False,
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='Reference of the sterilisation cycle record (e.g. autoclave '
             'cycle number).',
    )
    sterilisation_passed = fields.Boolean(
        copy=False,
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='The cycle met its acceptance criteria.',
    )

    # ------------------------------------------------------------------
    # CRUD: the stage mirrors the pharma state
    # ------------------------------------------------------------------
    def _pharma_stage_for(self, state):
        """Kanban stage shown for ``state``."""
        return self.env.ref(STAGE_BY_STATE[state], raise_if_not_found=False)

    @api.model_create_multi
    def create(self, vals_list):
        """Start every request as New, whatever stage the caller passed."""
        for vals in vals_list:
            state = vals.get('pharma_state') or 'new'
            stage = self._pharma_stage_for(state)
            if stage:
                vals['stage_id'] = stage.id
        return super().create(vals_list)

    def write(self, vals):
        """Keep the stage a mirror of the pharma state."""
        if 'stage_id' in vals and not self.env.context.get('pharma_stage_sync'):
            raise UserError(self.env._(
                'Move a maintenance request with its buttons (Start, Complete, '
                'QA Verify) rather than by changing its stage.'))
        if 'pharma_state' in vals:
            stage = self._pharma_stage_for(vals['pharma_state'])
            if stage:
                vals['stage_id'] = stage.id
            self = self.with_context(pharma_stage_sync=True)
        return super().write(vals)

    def archive_equipment_request(self):
        """Verified work is a GMP record and cannot be cancelled."""
        if self.filtered(lambda r: r.pharma_state == 'qa_verified'):
            raise UserError(self.env._('QA-verified maintenance cannot be cancelled.'))
        return super().archive_equipment_request()

    @api.ondelete(at_uninstall=False)
    def _unlink_except_verified(self):
        """Started or verified work stays on record."""
        if self.filtered(lambda r: r.pharma_state != 'new'):
            raise UserError(self.env._('Only a new maintenance request can be deleted; '
                                       'cancel it instead.'))

    def reset_equipment_request(self):
        """Reopen a cancelled request from New."""
        self.with_context(pharma_stage_sync=True).write({
            'archive': False,
            'pharma_state': 'new',
        })

    @api.depends('equipment_id', 'maintenance_type')
    def _compute_cleaning_settings(self):
        """Carry the clean and dirty holds over from the equipment's last cleaning."""
        for request in self:
            previous = request.equipment_id.sudo().last_cleaning_request_id
            if request.maintenance_type == 'cleaning' and previous:
                request.clean_hold_hours = previous.clean_hold_hours
                request.dirty_hold_hours = previous.dirty_hold_hours
            else:
                request.clean_hold_hours = 0
                request.dirty_hold_hours = 0

    @api.depends('equipment_id', 'maintenance_type')
    def _compute_sterilisation_settings(self):
        """Carry the method and hold over from the equipment's last sterilisation."""
        for request in self.sudo():
            previous = request.equipment_id.last_sterilisation_request_id
            cleaning = request.maintenance_type == 'cleaning'
            request.sterilisation_method = cleaning and previous.sterilisation_method
            request.sterile_hold_hours = previous.sterile_hold_hours if cleaning else 0

    @api.constrains('clean_hold_hours', 'dirty_hold_hours')
    def _check_cleaning_settings(self):
        """Hold times cannot be negative."""
        for request in self:
            if request.clean_hold_hours < 0 or request.dirty_hold_hours < 0:
                raise ValidationError(self.env._('The clean hold and dirty hold cannot be negative.'))

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_pharma_start(self):
        """Start the work. A cleaning puts the equipment in cleaning, and is
        flagged when the equipment's dirty hold has already run out."""
        for request in self:
            if request.pharma_state != 'new':
                raise UserError(self.env._('Only a new request can be started.'))
            if request.archive:
                raise UserError(self.env._('A cancelled request cannot be started.'))
            request.write({'pharma_state': 'in_progress'})
            equipment = request.equipment_id.sudo()
            if request.maintenance_type == 'cleaning' and equipment.cleaning_required:
                equipment._pharma_refresh_states()
                if equipment.cleaning_state == 'dirty_hold_expired':
                    request.dirty_hold_exceeded = True
                    request.message_post(body=self.env._(
                        'Cleaning started after the dirty hold ran out on %s. '
                        'QA to confirm the cleaning was effective.',
                        fields.Datetime.context_timestamp(
                            self, equipment.dirty_hold_until).strftime('%Y-%m-%d %H:%M')))
                equipment.cleaning_status = 'in_progress'

    def action_pharma_complete(self):
        """Engineering has finished; the request waits for QA."""
        for request in self:
            if request.pharma_state != 'in_progress':
                raise UserError(self.env._('Only a request in progress can be completed.'))
            if not request.equipment_id:
                raise UserError(self.env._('Select the equipment the work was done on.'))
            if not request.work_done:
                raise UserError(self.env._('Describe the work performed before completing.'))
            request._pharma_check_sterilisation_record()
            request.write({
                'pharma_state': 'completed',
                'completed_by': self.env.user.id,
                'completed_on': fields.Datetime.now(),
                'close_date': fields.Date.context_today(self),
            })
            request._pharma_request_qa_review()

    def _pharma_check_sterilisation_record(self):
        """A recorded sterilisation needs its method and cycle reference."""
        self.ensure_one()
        request = self.sudo()
        if request.maintenance_type == 'cleaning' and request.sterilisation_performed:
            if not request.sterilisation_method:
                raise UserError(self.env._('Enter the sterilisation method.'))
            if not request.sterilisation_cycle_ref:
                raise UserError(self.env._('Enter the sterilisation cycle reference.'))

    def _pharma_request_qa_review(self):
        """Ask a QA reviewer to verify the completed work."""
        self.ensure_one()
        qa_group = self.env.ref('pharmaceutical_base.group_pharma_role_qa')
        reviewer = qa_group.sudo().all_user_ids.filtered(
            lambda u: not u.share and u.active and u != self.env.user)[:1]
        if reviewer:
            self.activity_schedule(
                'pharma_equipment_maintenance.mail_activity_qa_verify',
                user_id=reviewer.id,
            )

    def action_qa_verify(self):
        """QA releases the equipment back to GMP use and records the result."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_qa_manager',
            self.env._('Only QA can verify maintenance work.'),
        )
        for request in self:
            if request.pharma_state != 'completed':
                raise UserError(self.env._('Only completed work can be QA verified.'))
            if request.completed_by == self.env.user:
                raise UserError(self.env._(
                    'The person who completed the work cannot verify it. '
                    'Ask another QA reviewer.'))
            request.write({
                'pharma_state': 'qa_verified',
                'qa_verified_by': self.env.user.id,
                'qa_verified_on': fields.Datetime.now(),
            })
            request.activity_feedback(['pharma_equipment_maintenance.mail_activity_qa_verify'])
            request._pharma_apply_result()

    def _pharma_apply_result(self):
        """Write the verified cleaning or repair to the equipment."""
        self.ensure_one()
        equipment = self.equipment_id.sudo()
        if not equipment:
            return
        if self.maintenance_type == 'cleaning' and equipment.cleaning_required:
            vals = {
                'cleaning_status': 'clean',
                'last_cleaning_request_id': self.id,
            }
            request = self.sudo()
            if (request.sterilisation_performed and request.sterilisation_passed
                    and equipment.sterilisation_required):
                vals['last_sterilisation_request_id'] = self.id
            equipment.write(vals)
        if self.requalification_required:
            today = fields.Date.context_today(self)
            equipment.write({'requalification_date': today})
            equipment.message_post(body=self.env._(
                'Requalification required after %(request)s, verified by %(user)s.',
                request=self.name, user=self.env.user.name))
        equipment._pharma_refresh_states()
