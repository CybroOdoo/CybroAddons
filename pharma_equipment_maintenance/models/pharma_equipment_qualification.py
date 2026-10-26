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
from odoo import api, fields, models
from odoo.exceptions import UserError

STAGES = [('iq', 'IQ'), ('oq', 'OQ'), ('pq', 'PQ')]
STAGE_LABEL = dict(STAGES)
STAGE_ORDER = {'iq': 10, 'oq': 20, 'pq': 30}
STAGE_TITLE = {
    'iq': 'Installation Qualification',
    'oq': 'Operational Qualification',
    'pq': 'Performance Qualification',
}


class PharmaEquipmentQualification(models.Model):
    """One IQ, OQ or PQ record; generated when GMP critical equipment is registered.

    Like SOP training records: registering the equipment creates the three
    records as Pending. QA signs them off in order (IQ, OQ, PQ) and each
    outcome is written back to the equipment, so the IQ/OQ/PQ flags always
    rest on a signed record rather than a tick box.
    """
    _name = 'pharma.equipment.qualification'
    _description = 'Equipment Qualification Record'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _order = 'equipment_id, id desc, sequence'

    equipment_id = fields.Many2one(
        comodel_name='maintenance.equipment', 
        required=True, ondelete='cascade', index=True, tracking=True)
    company_id = fields.Many2one(
        related='equipment_id.company_id', store=True, string='Company')
    stage = fields.Selection(
        selection=STAGES, required=True, readonly=True, tracking=True)
    sequence = fields.Integer(compute='_compute_sequence', store=True)
    name = fields.Char(string='Record', compute='_compute_name', store=True)
    state = fields.Selection(
        selection=[('pending', 'Pending'), ('passed', 'Passed'), ('failed', 'Failed')],
        string='Status', default='pending', required=True, readonly=True,
        copy=False, tracking=True)
    protocol_ref = fields.Char(
        related='equipment_id.qualification_protocol_ref', string='Qualification Protocol')
    performed_on = fields.Date(
        copy=False, tracking=True,
        help='Date the qualification stage was executed.')
    report_ref = fields.Char(
        string='Report Reference', copy=False, tracking=True,
        help='Reference of the executed IQ/OQ/PQ report.')
    report_attachment = fields.Binary(string='Report', attachment=True, copy=False)
    report_attachment_name = fields.Char(string='Report File Name', copy=False)
    notes = fields.Text(string='Findings', copy=False)
    signed_by = fields.Many2one(
        comodel_name='res.users', string='Signed Off By', readonly=True, copy=False, tracking=True)
    signed_on = fields.Datetime(string='Signed Off On', readonly=True, copy=False)
    active = fields.Boolean(default=True, tracking=True)

    @api.depends('stage')
    def _compute_sequence(self):
        """Order the records IQ, OQ, PQ."""
        for rec in self:
            rec.sequence = STAGE_ORDER.get(rec.stage, 0)

    @api.depends('stage', 'equipment_id.name')
    def _compute_name(self):
        """Name the record after its stage and equipment."""
        for rec in self:
            rec.name = '%s - %s' % (
                STAGE_LABEL.get(rec.stage, ''), rec.equipment_id.display_name or '')

    # ------------------------------------------------------------------
    # Sign-off
    # ------------------------------------------------------------------
    def _check_sign_off(self):
        """Only QA signs off, and only a complete, pending record."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_qa_manager',
            self.env._('Only QA can sign off a qualification stage.'))
        for rec in self:
            if rec.state != 'pending':
                raise UserError(self.env._('Only a pending record can be signed off.'))
            if not rec.active:
                raise UserError(self.env._('An archived record cannot be signed off.'))
            if not rec.performed_on:
                raise UserError(self.env._('Enter the date the stage was performed.'))
            if rec.performed_on > fields.Date.context_today(self):
                raise UserError(self.env._('The performed date cannot be in the future.'))
            if not rec.report_ref:
                raise UserError(self.env._('Enter the report reference.'))

    def action_pass(self):
        """QA accepts the stage; IQ must pass before OQ, OQ before PQ."""
        self._check_sign_off()
        for rec in self:
            earlier = rec.equipment_id.qualification_ids.filtered(
                lambda r: r.sequence < rec.sequence and r.state != 'passed')
            if earlier:
                raise UserError(self.env._(
                    '%(stage)s cannot pass before %(earlier)s has passed.',
                    stage=STAGE_LABEL[rec.stage],
                    earlier=', '.join(earlier.mapped(lambda r: STAGE_LABEL[r.stage]))))
            rec._sign('passed')

    def action_fail(self):
        """QA rejects the stage; it can be reopened once corrected."""
        self._check_sign_off()
        for rec in self:
            if not (rec.notes or '').strip():
                raise UserError(self.env._('Describe the findings of a failed stage.'))
            rec._sign('failed')

    def action_reopen(self):
        """Reopen a failed stage for re-execution."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_qa_manager',
            self.env._('Only QA can reopen a qualification stage.'))
        for rec in self:
            if rec.state != 'failed':
                raise UserError(self.env._('Only a failed record can be reopened.'))
            rec.write({'state': 'pending', 'signed_by': False, 'signed_on': False})

    def _sign(self, state):
        """Record the outcome and write it back to the equipment."""
        self.ensure_one()
        self.write({
            'state': state,
            'signed_by': self.env.user.id,
            'signed_on': fields.Datetime.now(),
        })
        self.equipment_id.sudo()._pharma_sync_qualification(self)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_signed(self):
        """Signed records stay on file."""
        if self.filtered(lambda r: r.state != 'pending'):
            raise UserError(self.env._('Signed qualification records are GMP records; archive them instead.'))
