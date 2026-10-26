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
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

# Fields fixed when the sample is recorded (or by the disposal action). They
# are only written by this module's own flows, under INTERNAL_CTX.
PROTECTED_FIELDS = {
    'name', 'lot_id', 'qa_release_id', 'production_id', 'state',
    'retained_qty',
    'retained_by', 'retained_on', 'retention_period_months',
    'exam_interval_months', 'last_exam_date', 'next_exam_date',
    'disposed_by', 'disposed_on', 'disposal_method', 'disposal_reference',
    'disposal_note',
}
INTERNAL_CTX = 'pharma_retention_internal'
# Proposed on creation and still adjustable until the sample is confirmed.
DRAFT_EDITABLE_FIELDS = {'retained_qty'}


class PharmaRetentionSample(models.Model):
    """Reserve (retention) sample register entry for one released batch.

    The sample's place is recorded against an internal stock location, but it
    is not stock: no quant or stock move is created for it, so it never shows
    in on-hand or valuation reports.
    Records are never deleted — disposal is a state on the register.
    """
    _name = 'pharma.retention.sample'
    _description = 'Retention Sample'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _order = 'retained_on desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default='New', tracking=True,
                       help='Register number of the reserve sample.')
    lot_id = fields.Many2one('stock.lot', string='Batch', required=True,
                             readonly=True, index=True, ondelete='restrict',
                             tracking=True, help='Released batch the sample was taken from.')
    product_id = fields.Many2one('product.product', related='lot_id.product_id',
                                 store=True, string='Product',
                                 help='Product of the batch.')
    product_uom_id = fields.Many2one('uom.uom', related='lot_id.product_uom_id',
                                     string='Unit', help='Unit of measure of all quantities.')
    qa_release_id = fields.Many2one('pharma.qa.release', string='QA Release',
                                    readonly=True, help='QA release record of the batch.')
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order',
                                    readonly=True, help='Manufacturing order of the batch.')
    company_id = fields.Many2one('res.company', required=True,
                                 default=lambda self: self.env.company,
                                 help='Company holding the sample.')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('retained', 'Retained'),
        ('disposed', 'Disposed'),
    ], string='Status', default='draft', required=True, readonly=True,
        tracking=True, help='Draft until the storage location is set and the '
                            'sample confirmed; retained until an approved '
                            'disposal is recorded.')

    # Quantities
    retained_qty = fields.Float(string='Quantity Retained', digits='Product Unit',
                                tracking=True,
                                help='Quantity actually set aside.')
    withdrawn_qty = fields.Float(string='Withdrawn', digits='Product Unit',
                                 compute='_compute_quantities', store=True,
                                 help='Total quantity withdrawn so far.')
    remaining_qty = fields.Float(string='Remaining', digits='Product Unit',
                                 compute='_compute_quantities', store=True,
                                 help='Quantity still held.')

    # Storage
    container = fields.Char(tracking=True,
                            help='Container the sample is held in.')
    location_id = fields.Many2one('stock.location',
                                  tracking=True, ondelete='restrict',
                                  domain="[('usage', '=', 'internal'), ('pharma_is_retention_location', '=', True)]",
                                  help='Where the sample is physically held. '
                                       'Required to confirm the sample.')
    retained_by = fields.Many2one('res.users', readonly=True,
                                  help='Person who recorded the sample.')
    retained_on = fields.Datetime(readonly=True,
                                  help='When the sample was recorded.')

    # Retention period
    expiry_date = fields.Date(related='lot_id.expiry_date', store=True,
                              string='Batch Expiry', help='Expiry date of the batch.')
    retention_period_months = fields.Integer(
        string='Held Beyond Expiry (Months)', readonly=True,
        help='Retention period applied when the sample was recorded.')
    disposal_due_date = fields.Date(string='Disposal Due', compute='_compute_disposal_due_date',
                                    store=True, tracking=True,
                                    help='Batch expiry plus the retention period.')
    is_disposal_due = fields.Boolean(string='Due for Disposal', compute='_compute_is_disposal_due',
                                     help='The retention period has expired.')

    # Periodic examination
    exam_interval_months = fields.Integer(string='Examination Every (Months)', readonly=True,
                                          help='Interval between visual examinations.')
    last_exam_date = fields.Date(string='Last Examined', readonly=True, tracking=True,
                                 help='Date of the last periodic visual examination.')
    next_exam_date = fields.Date(string='Next Examination', readonly=True, tracking=True,
                                 help='Date the next periodic visual examination falls due.')

    withdrawal_ids = fields.One2many('pharma.retention.withdrawal', 'sample_id',
                                     string='Withdrawals', readonly=True,
                                     help='History of quantities taken from the sample.')

    # Disposal
    disposed_by = fields.Many2one('res.users', string='Disposal Approved By', readonly=True,
                                  help='Quality manager who approved the disposal.')
    disposed_on = fields.Datetime(readonly=True,
                                  help='When the disposal was recorded.')
    disposal_method = fields.Selection([
        ('incineration', 'Incineration'),
        ('chemical', 'Chemical Destruction'),
        ('contractor', 'Licensed Waste Contractor'),
        ('other', 'Other'),
    ], readonly=True, help='How the sample was destroyed.')
    disposal_reference = fields.Char(readonly=True,
                                     help='Destruction certificate or waste note number.')
    disposal_note = fields.Text(string='Disposal Remarks', readonly=True,
                                help='Remarks recorded with the disposal.')

    @api.depends('retained_qty', 'withdrawal_ids.quantity')
    def _compute_quantities(self):
        """Derive the withdrawn and remaining quantities."""
        for rec in self:
            rec.withdrawn_qty = sum(rec.withdrawal_ids.mapped('quantity'))
            rec.remaining_qty = rec.retained_qty - rec.withdrawn_qty

    @api.depends('expiry_date', 'retention_period_months')
    def _compute_disposal_due_date(self):
        """Disposal falls due once the retention period after expiry has run."""
        for rec in self:
            rec.disposal_due_date = (
                rec.expiry_date + relativedelta(months=rec.retention_period_months)
                if rec.expiry_date else False)

    @api.depends('state', 'disposal_due_date')
    def _compute_is_disposal_due(self):
        """Flag retained samples whose disposal date has been reached."""
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_disposal_due = bool(rec.state == 'retained' and rec.disposal_due_date
                                       and rec.disposal_due_date <= today)

    @api.model_create_multi
    def create(self, vals_list):
        """Number the sample."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pharma.retention.sample') or 'New'
        return super().create(vals_list)

    def write(self, vals):
        """Protect the register: recorded facts change only through its own actions."""
        if not self.env.context.get(INTERNAL_CTX):
            protected = PROTECTED_FIELDS & set(vals)
            if all(rec.state == 'draft' for rec in self):
                protected -= DRAFT_EDITABLE_FIELDS
            if protected:
                raise UserError(self.env._(
                    "Recorded retention sample details cannot be edited directly. "
                    "Use Record Withdrawal or Dispose instead."))
            if any(rec.state == 'disposed' for rec in self):
                raise UserError(self.env._("A disposed retention sample can no longer be changed."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        """The register keeps every sample; disposal is recorded, not deleted."""
        raise UserError(self.env._(
            "Retention samples are never deleted. Record a disposal instead."))

    @api.model
    def _pharma_create_for_lot(self, lot):
        """Create the draft reserve sample of a released batch from its product's rule.

        Container and location are proposed from the rule; the quantity and
        location are confirmed (or chosen) on the sample before it counts as
        retained.
        """
        if lot.lot_status != 'released':
            raise UserError(self.env._("Batch %s has not been released.", lot.name))
        if lot.retention_sample_ids:
            raise UserError(self.env._("A reserve sample is already recorded for batch %s.", lot.name))
        tmpl = lot.product_id.product_tmpl_id
        qa_release = self.env['pharma.qa.release'].search(
            [('lot_id', '=', lot.id)], order='id desc', limit=1)
        company = lot.company_id or self.env.company
        return self.with_context(**{INTERNAL_CTX: True}).create({
            'lot_id': lot.id,
            'qa_release_id': qa_release.id,
            'production_id': qa_release.production_id.id,
            'company_id': company.id,
            'container': tmpl.retention_container,
            'location_id': (tmpl.retention_location_id
                            or company.pharma_retention_location_id).id,
            'retention_period_months': tmpl.retention_period_months,
            'exam_interval_months': tmpl.retention_exam_interval_months,
        })

    def action_confirm(self):
        """Confirm the sample as retained; its storage location must be set."""
        activity_type = self.env.ref('pharma_retention_sample.mail_activity_retain_sample',
                                     raise_if_not_found=False)
        now = fields.Datetime.now()
        today = fields.Date.context_today(self)
        for sample in self:
            if sample.state != 'draft':
                raise UserError(self.env._("Retention sample %s is already confirmed.", sample.name))
            if not sample.location_id:
                raise UserError(self.env._(
                    "Set the location where reserve sample %s is held before "
                    "confirming it.", sample.name))
            if float_compare(sample.retained_qty, 0.0,
                             precision_rounding=sample.product_uom_id.rounding or 0.0001) <= 0:
                raise UserError(self.env._("Enter the quantity set aside."))
            interval = sample.exam_interval_months
            sample.with_context(**{INTERNAL_CTX: True}).write({
                'state': 'retained',
                'retained_by': self.env.user.id,
                'retained_on': now,
                'next_exam_date': today + relativedelta(months=interval) if interval else False,
            })
            if activity_type:
                sample.lot_id.sudo().activity_ids.filtered(
                    lambda a: a.activity_type_id == activity_type
                ).action_feedback(feedback=self.env._("Reserve sample %s recorded.", sample.name))
            # Users recording samples may have no write access on stock.lot.
            sample.lot_id.sudo().message_post(author_id=self.env.user.partner_id.id, body=self.env._(
                "Reserve sample %(ref)s recorded: %(qty)s %(uom)s at %(loc)s.",
                ref=sample.name, qty=sample.retained_qty,
                uom=sample.product_uom_id.name, loc=sample.location_id.display_name))
        return True

    def _pharma_after_withdrawal(self, withdrawal):
        """Roll the examination schedule forward after a periodic examination."""
        self.ensure_one()
        if withdrawal.purpose == 'periodic_exam':
            vals = {'last_exam_date': withdrawal.date}
            if self.exam_interval_months:
                vals['next_exam_date'] = withdrawal.date + relativedelta(
                    months=self.exam_interval_months)
            self.with_context(**{INTERNAL_CTX: True}).write(vals)
            if withdrawal.exam_result == 'unsatisfactory':
                self.message_post(body=self.env._(
                    "Periodic examination on %s was UNSATISFACTORY. Consider "
                    "raising a deviation for this batch.", withdrawal.date))

    def action_record_withdrawal(self):
        """Open the withdrawal form in a dialog."""
        self.ensure_one()
        if self.state != 'retained':
            raise UserError(self.env._("Nothing can be withdrawn from a disposed sample."))
        return {
            'name': self.env._('Record Withdrawal'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.retention.withdrawal',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sample_id': self.id},
        }

    def action_open_disposal_wizard(self):
        """Open the approved-disposal wizard (quality management only)."""
        self.ensure_one()
        self._check_pharma_group('pharmaceutical_base.group_pharma_role_qa',
                                 self.env._("Only quality management can dispose of a retention sample."))
        return {
            'name': self.env._('Dispose Retention Sample'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.retention.disposal.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sample_id': self.id},
        }

    def action_view_lot(self):
        """Open the batch the sample was taken from."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'form',
            'res_id': self.lot_id.id,
        }

    @api.model
    def _cron_pharma_missing_retention(self):
        """Daily: remind the releasing user of released batches with no reserve sample.

        Release is not held up by a missing sample; this makes the gap visible
        instead. One open reminder per batch — existing ones are not repeated.
        """
        activity_type = self.env.ref('pharma_retention_sample.mail_activity_retain_sample',
                                     raise_if_not_found=False)
        lots = self.env['stock.lot'].search(self.env['stock.lot']._pharma_retention_missing_domain())
        fallback_user = self.env.ref('base.user_admin', raise_if_not_found=False)
        for lot in lots:
            if activity_type and lot.activity_ids.filtered(
                    lambda a: a.activity_type_id == activity_type):
                continue
            user = lot.status_changed_by or fallback_user
            if not user:
                continue
            lot.activity_schedule(
                'pharma_retention_sample.mail_activity_retain_sample',
                user_id=user.id,
                note=self.env._("Batch %s was released but no reserve sample has been "
                       "confirmed. Use the Retention Sample button on the batch or "
                       "its QA release, then set the quantity and location and confirm it.", lot.name))
