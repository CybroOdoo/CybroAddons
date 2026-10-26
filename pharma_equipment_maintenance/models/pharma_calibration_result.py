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
from datetime import timedelta

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

RESULT = [('pass', 'Within Tolerance'), ('fail', 'Out of Tolerance')]
OPEN_STATES = ('new', 'in_progress')
# Fields the workflow writes once the calibration is no longer open.
WORKFLOW_FIELDS = {
    'state', 'completed_by', 'completed_on', 'qa_verified_by', 'qa_verified_on',
    'impact_reference_date', 'message_main_attachment_id',
}


class PharmaCalibrationResult(models.Model):
    """One calibration of an instrument, from the work to QA release.

    Moves New -> In Progress -> Completed -> QA Verified. QA verification
    applies the outcome to the equipment: a pass sets its calibration dates,
    a failure puts it out of calibration, and an as-found failure raises the
    impact assessment on the results measured since the previous calibration.
    """
    _name = 'pharma.calibration.result'
    _description = 'Calibration'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _order = 'calibration_performed_on desc, id desc'

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default='New', index=True)
    equipment_id = fields.Many2one(
        comodel_name='maintenance.equipment', required=True,
        index=True, tracking=True, ondelete='restrict',
        domain="[('calibration_required', '=', True)]",
        help='Instrument that was calibrated.')
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('qa_verified', 'QA Verified'),
        ],
        string='Status', default='new', required=True, readonly=True,
        copy=False, tracking=True,
        help='New, In Progress, Completed by engineering, then QA Verified: '
             'only then is the outcome applied to the equipment.')
    company_id = fields.Many2one(
        related='equipment_id.company_id', store=True, string='Company')
    calibration_performed_on = fields.Date(
        string='Calibrated On', required=True, tracking=True,
        default=fields.Date.context_today,
        help='Date the calibration was performed.')
    calibration_passed = fields.Boolean(
        compute='_compute_calibration_results',
        store=True, tracking=True,
        help='Every check point left in tolerance. A failed calibration puts '
             'the instrument out of calibration on QA verification.')
    calibration_frequency_days = fields.Integer(
        string='Calibration Interval (Days)', compute='_compute_calibration_settings',
        store=True, readonly=False, precompute=True, tracking=True,
        help='Days from this calibration to the next one. Taken from the '
             'previous calibration of the equipment.')
    calibration_reminder_days = fields.Integer(
        string='Calibration Reminder (Days)', compute='_compute_calibration_settings',
        store=True, readonly=False, precompute=True, tracking=True,
        help='Days before the next calibration that the equipment shows as '
             'due soon and a reminder is raised.')
    next_calibration_date = fields.Date(
        string='Next Calibration', compute='_compute_next_calibration_date', store=True,
        help='Calibration date plus the calibration interval.')
    certificate_number = fields.Char(
        tracking=True,
        help='Number of the calibration certificate.')
    certificate_attachment = fields.Binary(
        string='Certificate', attachment=True, copy=False,
        help='Scan of the calibration certificate.')
    certificate_attachment_name = fields.Char(string='Certificate File Name', copy=False)
    point_ids = fields.One2many(
        comodel_name='pharma.calibration.point', inverse_name='result_id',
        string='Results', copy=False,
        help='Points measured against certified standards. They decide '
             'whether the calibration passed.')
    calibration_as_found_result = fields.Selection(
        selection=RESULT, string='As-Found Result', compute='_compute_calibration_results',
        store=True, tracking=True,
        help='Did the instrument arrive in tolerance? When out of tolerance the '
             'instrument is fine now, but results measured since the previous '
             'calibration are suspect.')
    calibration_as_left_result = fields.Selection(
        selection=RESULT, string='As-Left Result', compute='_compute_calibration_results',
        store=True, tracking=True,
        help='Did the instrument leave in tolerance? When out of tolerance it '
             'cannot be used.')
    notes = fields.Text()
    completed_by = fields.Many2one(
        comodel_name='res.users', readonly=True,
        copy=False, tracking=True,
        help='Who marked the calibration completed.')
    completed_on = fields.Datetime(
        readonly=True, copy=False, tracking=True,
        help='When the calibration was marked completed.')
    qa_verified_by = fields.Many2one(
        comodel_name='res.users', string='QA Verified By', readonly=True,
        copy=False, tracking=True,
        help='QA reviewer who applied the calibration to the equipment.')
    qa_verified_on = fields.Datetime(
        string='QA Verified On', readonly=True, copy=False, tracking=True,
        help='When QA verified the calibration.')
    impact_reference_date = fields.Date(
        string='Suspect Results From Calibration', readonly=True, copy=False,
        help='Set when an as-found failure is verified: the previous passed '
             'calibration. The QC results measured under it are the ones to assess.')

    @api.depends('equipment_id')
    def _compute_calibration_settings(self):
        """Carry the interval and reminder over from the equipment's previous calibration."""
        for result in self:
            previous = self.search([
                ('equipment_id', '=', result.equipment_id.id),
                ('id', '!=', result._origin.id),
            ], limit=1) if result.equipment_id else self.browse()
            result.calibration_frequency_days = previous.calibration_frequency_days or 365
            result.calibration_reminder_days = (
                previous.calibration_reminder_days if previous else 30)

    @api.depends('calibration_performed_on', 'calibration_frequency_days')
    def _compute_next_calibration_date(self):
        """Calibration date plus the calibration interval."""
        for result in self:
            result.next_calibration_date = (
                result.calibration_performed_on
                + timedelta(days=result.calibration_frequency_days)
                if result.calibration_performed_on and result.calibration_frequency_days > 0
                else False)

    @api.constrains('calibration_frequency_days', 'calibration_reminder_days')
    def _check_calibration_settings(self):
        """The interval must be positive and the reminder cannot be negative."""
        for result in self:
            if result.calibration_frequency_days <= 0:
                raise ValidationError(self.env._('Set a calibration interval greater than zero.'))
            if result.calibration_reminder_days < 0:
                raise ValidationError(self.env._('The calibration reminder cannot be negative.'))

    @api.depends('point_ids.as_found_result', 'point_ids.as_left_result')
    def _compute_calibration_results(self):
        """Derive the outcomes from the points; nothing is derived without points."""
        for result in self:
            points = result.point_ids
            result.calibration_passed = bool(points) and 'fail' not in points.mapped('as_left_result')
            result.calibration_as_found_result = (
                False if not points else
                'fail' if 'fail' in points.mapped('as_found_result') else 'pass')
            result.calibration_as_left_result = (
                False if not points else
                'fail' if 'fail' in points.mapped('as_left_result') else 'pass')

    @api.constrains('calibration_performed_on')
    def _check_calibration_date(self):
        """A calibration cannot be recorded ahead of time."""
        today = fields.Date.context_today(self)
        for result in self:
            if result.calibration_performed_on and result.calibration_performed_on > today:
                raise ValidationError(self.env._('The calibration date cannot be in the future.'))

    def _check_open(self):
        """The calibration is a record of the work: editable only while it is open."""
        closed = self.filtered(lambda r: r.state not in OPEN_STATES)
        if closed:
            raise UserError(self.env._(
                'A calibration cannot be changed once it is completed: %s.',
                ', '.join(closed.mapped('name'))))

    @api.model_create_multi
    def create(self, vals_list):
        """Number the calibration."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pharma.calibration.result') or 'New'
        return super().create(vals_list)

    def write(self, vals):
        """Lock the calibration once the work is completed."""
        if not set(vals) <= WORKFLOW_FIELDS:
            self._check_open()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_closed(self):
        """A completed calibration stays on record."""
        self._check_open()

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_start(self):
        """Start the calibration."""
        for result in self:
            if result.state != 'new':
                raise UserError(self.env._('Only a new calibration can be started.'))
            result.state = 'in_progress'

    def action_complete(self):
        """Engineering has finished; the calibration waits for QA."""
        for result in self:
            if result.state != 'in_progress':
                raise UserError(self.env._('Only a calibration in progress can be completed.'))
            if not result.point_ids:
                raise UserError(self.env._('Enter the calibration results before completing.'))
            if result.calibration_passed and not result.certificate_number:
                raise UserError(self.env._('Enter the calibration certificate number.'))
            result.write({
                'state': 'completed',
                'completed_by': self.env.user.id,
                'completed_on': fields.Datetime.now(),
            })
            result._request_qa_review()

    def _request_qa_review(self):
        """Ask a QA reviewer to verify the completed calibration."""
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
        """QA applies the calibration to the equipment."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_qa_manager',
            self.env._('Only QA can verify a calibration.'),
        )
        for result in self:
            if result.state != 'completed':
                raise UserError(self.env._('Only a completed calibration can be QA verified.'))
            if result.completed_by == self.env.user:
                raise UserError(self.env._(
                    'The person who completed the calibration cannot verify it. '
                    'Ask another QA reviewer.'))
            result.sudo().write({
                'state': 'qa_verified',
                'qa_verified_by': self.env.user.id,
                'qa_verified_on': fields.Datetime.now(),
            })
            result.sudo().activity_feedback(['pharma_equipment_maintenance.mail_activity_qa_verify'])
            result._apply_to_equipment()
        # An as-found failure puts the suspect results in front of QA straight away.
        if len(self) == 1 and self.calibration_as_found_result == 'fail':
            return self.action_calibration_impact_assessment()

    def _apply_to_equipment(self):
        """Write the verified calibration to the equipment."""
        self.ensure_one()
        equipment = self.equipment_id.sudo()
        previous_calibration = equipment.last_calibration_date
        if self.calibration_passed:
            equipment.write({
                'last_calibration_result_id': self.id,
                'calibration_failed_on': False,
            })
            equipment.message_post(body=self.env._(
                'Calibration passed on %(date)s (certificate %(cert)s), '
                'verified by %(user)s.',
                date=self.calibration_performed_on, cert=self.certificate_number,
                user=self.env.user.name))
        else:
            equipment.write({'calibration_failed_on': self.calibration_performed_on})
            count = equipment.impacted_result_count
            equipment.message_post(body=Markup('<p>%s</p><p>%s</p>') % (
                self.env._('Calibration FAILED on %s. The instrument is out of '
                           'calibration.', self.calibration_performed_on),
                self.env._('%s result(s) were measured with it since its last passed '
                           'calibration. Run the Calibration Impact Assessment from '
                           'the equipment.', count)))
        if self.calibration_as_found_result == 'fail':
            self.sudo().impact_reference_date = previous_calibration
            self._raise_impact_assessment()
        equipment._pharma_refresh_states()

    # ------------------------------------------------------------------
    # Impact assessment (as-found out of tolerance)
    # ------------------------------------------------------------------
    def _impacted_results(self):
        """QC results measured under the calibration this one found out of tolerance."""
        self.ensure_one()
        equipment = self.equipment_id.sudo()
        return self.env['pharma.qc.result.line'].sudo().search(
            equipment._impacted_result_domain_for(self.impact_reference_date))

    def _raise_impact_assessment(self):
        """As-found failed: tell everyone the earlier results are suspect and ask QA to assess them."""
        self.ensure_one()
        results = self._impacted_results()
        orders = results.test_order_id
        previous = self.impact_reference_date
        body = Markup('<p>%s</p><p>%s</p>') % (
            self.env._('As-found OUT OF TOLERANCE at the calibration of %s. The instrument is '
                       'fine now, but earlier results are suspect.', self.calibration_performed_on),
            self.env._('%(results)s result(s) in %(orders)s QC test(s) were measured since the previous '
                       'calibration%(since)s. Run the Calibration Impact Assessment.',
                       results=len(results), orders=len(orders),
                       since=self.env._(' of %s', previous) if previous else ''))
        self.sudo().message_post(body=body)
        self.equipment_id.sudo().message_post(body=body)
        self.sudo().activity_schedule(
            'pharma_equipment_maintenance.mail_activity_calibration_impact',
            user_id=self.env.user.id,
            note=self.env._('%(count)s result(s) measured with %(equipment)s since its previous calibration '
                            'are suspect. Assess the impact on the released batches.',
                            count=len(results), equipment=self.equipment_id.display_name))

    def action_calibration_impact_assessment(self):
        """The QC results this calibration found suspect (as-found out of tolerance)."""
        self.ensure_one()
        equipment = self.equipment_id
        previous = self.impact_reference_date
        since = (self.env._('calibration of %s', previous) if previous
                 else self.env._('no earlier calibration'))
        return equipment._pharma_impact_action(
            equipment._impacted_result_domain_for(previous),
            self.env._('Calibration Impact: %(equipment)s (%(since)s)',
                       equipment=equipment.display_name, since=since))
