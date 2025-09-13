# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
import logging
_logger = logging.getLogger(__name__)



class GymMembership(models.Model):
    """This model is for gym membership."""
    _name = "gym.membership"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Gym Membership"
    _rec_name = "reference"

    reference = fields.Char(string='GYM reference', readonly=True,
                            default=lambda self: _('New'),
                            help="Member reference")
    member_id = fields.Many2one('res.partner', string='Member',
                                required=True, tracking=True,
                                help="Member taken the membership",
                                domain="[('is_gym_member', '!=',False)]")
    membership_scheme_id = fields.Many2one('product.product',
                                           string='Membership scheme',
                                           help="Member ship scheme",
                                           required=True, tracking=True,
                                           domain="[('membership_date_from', "
                                                  "'!=',False)]")

    membership_duration = fields.Integer(
        string='Plan Duration (Days)',
        compute='_compute_membership_duration',
    )

    paid_amount = fields.Monetary(
        string="Paid Amount",
        compute="_compute_paid_amount",
        store=True,
        currency_field="company_currency_id",
        tracking=True,
    )

    company_currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True
    )
    membership_fees = fields.Float(string="Membership Fees", tracking=True,
                                   help="The membership fees",
                                   related="membership_scheme_id.list_price")
    sale_order_id = fields.Many2one('sale.order', string='Sales Order',
                                    ondelete='cascade', copy=False,
                                    help="Order reference",
                                    readonly=True)
    membership_date_from = fields.Date(string='Membership Start Date',
                                       related="membership_scheme_id."
                                               "membership_date_from",
                                       help='Date from which membership '
                                            'becomes active.')
    membership_date_to = fields.Date(string='Membership End Date',
                                     related="membership_scheme_id.membership_"
                                             "date_to",
                                     help='Date until which membership remains'
                                          'active.')
    effective_start_date = fields.Date(string='Effective Start Date',
                                       compute='_compute_effective_dates',
                                       help='Actual start date considering pauses')
    effective_end_date = fields.Date(string='Effective End Date',
                                     compute='_compute_effective_dates',
                                     help='Actual end date considering pauses and extensions')
    current_pause_start = fields.Date(string='Current Pause Start Date',
                                      help='Start date of current pause period')
    total_paused_days = fields.Integer(string='Total Paused Days', default=0,
                                       help='Total number of days this membership has been paused')
    pause_history_ids = fields.One2many('gym.membership.pause', 'membership_id',
                                        string='Pause History')
    extension_history_ids = fields.One2many('gym.membership.extension', 'membership_id',
                                            string='Extension History')
    total_extended_days = fields.Integer(string='Total Extended Days', default=0,
                                         help='Total number of days this membership has been extended')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help='The field hold the company id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status',
        tracking=True,
        help="The status of record defined here")

    extension_count = fields.Integer(
        string='Extension Count',
        compute='_compute_extension_count',
        help='Number of times this membership has been extended'
    )

    can_extend = fields.Boolean(
        string='Can Extend',
        compute='_compute_can_extend'
    )

    _sql_constraints = [
        ('membership_date_greater',
         'check(membership_date_to >= membership_date_from)',
         'Error ! Ending Date cannot be set before Beginning Date.')
    ]

    @api.depends('state', 'effective_end_date')
    def _compute_can_extend(self):
        """Compute if membership can be extended (only if expired)"""
        for rec in self:
            rec.can_extend = rec.state == 'expired'

    @api.depends('membership_date_from', 'membership_date_to', 'total_paused_days', 'total_extended_days')
    def _compute_effective_dates(self):
        """Compute effective start and end dates based on pauses and extensions"""
        for rec in self:
            rec.effective_start_date = rec.membership_date_from
            if rec.membership_date_to:
                additional_days = rec.total_paused_days + rec.total_extended_days
                rec.effective_end_date = rec.membership_date_to + timedelta(days=additional_days)
            else:
                rec.effective_end_date = rec.membership_date_to

    @api.model_create_multi
    def create(self, vals_list):
        """Sequence number for membership """
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'gym.membership') or 'New'
        return super(GymMembership, self).create(vals_list)

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def action_set_active(self):
        for rec in self:
            rec.state = 'active'

    def action_pause(self):
        """Pause the membership - only from active state"""
        for rec in self:
            if rec.state != 'active':
                raise UserError(_('Only active memberships can be paused.'))
            current_attendance = self.env['gym.attendance'].search([
                ('member_id', '=', rec.member_id.id),
                ('check_out', '=', False)
            ], limit=1)

            if current_attendance:
                current_attendance.write({
                    'check_out': fields.Datetime.now()
                })

                rec.message_post(
                    body=_('Member automatically checked out at %s due to membership pause.') %
                         fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    message_type='notification'
                )

            rec.current_pause_start = date.today()
            rec.state = 'paused'
            rec.message_post(
                body=_('Membership paused on %s') % date.today().strftime('%Y-%m-%d'),
                message_type='notification'
            )

    def action_resume(self):
        """Resume the membership from paused state"""
        for rec in self:
            if rec.state != 'paused':
                raise UserError(_('Only paused memberships can be resumed.'))

            if not rec.current_pause_start:
                raise UserError(_('No pause start date found.'))

            pause_end = date.today()
            paused_days = (pause_end - rec.current_pause_start).days

            self.env['gym.membership.pause'].create({
                'membership_id': rec.id,
                'pause_start': rec.current_pause_start,
                'pause_end': pause_end,
                'days_paused': paused_days,
            })

            rec.total_paused_days += paused_days

            rec.current_pause_start = False
            rec.state = 'active'

            rec.message_post(
                body=_('Membership resumed on %s. Paused for %s days.') % (
                    pause_end.strftime('%Y-%m-%d'), paused_days
                ),
                message_type='notification'
            )

    def _auto_checkout_member(self, reason="membership status change"):
        """Helper method to automatically check out a member"""
        self.ensure_one()

        current_attendance = self.env['gym.attendance'].search([
            ('member_id', '=', self.member_id.id),
            ('check_out', '=', False)
        ], limit=1)

        if current_attendance:
            current_attendance.write({
                'check_out': fields.Datetime.now()
            })

            self.message_post(
                body=_('Member automatically checked out at %s due to %s') %
                     (fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reason),
                message_type='notification'
            )

            return True
        return False

    def action_expire(self):
        """Expire the membership and auto check-out if needed"""
        for rec in self:
            rec._auto_checkout_member("membership expiry")

            rec.state = 'expired'

            rec.message_post(
                body=_('Membership expired on %s') % date.today().strftime('%Y-%m-%d'),
                message_type='notification'
            )

    def action_cancel(self):
        """Cancel the membership and auto check-out if needed"""
        for rec in self:
            rec._auto_checkout_member("membership cancellation")

            rec.state = 'cancelled'

    def action_extend_membership(self):
        """Open wizard to extend membership - only for expired memberships"""
        self.ensure_one()
        if self.state != 'expired':
            raise UserError(_('Only expired memberships can be extended.'))

        recent_extension = self.env['gym.membership.extension'].search([
            ('membership_id', '=', self.id),
            ('extension_date', '>', fields.Date.today() - timedelta(days=30))  # Within last 30 days
        ], limit=1)

        if recent_extension:
            raise UserError(_(
                'This membership was already extended on %s. '
                'You cannot extend again within 30 days of the last extension.'
            ) % recent_extension.extension_date.strftime('%Y-%m-%d'))

        return {
            'name': _('Extend Membership'),
            'type': 'ir.actions.act_window',
            'res_model': 'gym.membership.extend.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_membership_id': self.id,
                'default_member_id': self.member_id.id,
            }
        }

    def force_checkout_inactive_members(self):
        """
        Manual method to force check-out all members who are checked in
        but have inactive memberships (paused, expired, cancelled)
        """
        inactive_memberships = self.search([
            ('state', 'in', ['paused', 'expired', 'cancelled'])
        ])

        checkout_count = 0
        for membership in inactive_memberships:
            current_attendance = self.env['gym.attendance'].search([
                ('member_id', '=', membership.member_id.id),
                ('check_out', '=', False)
            ])

            if current_attendance:
                current_attendance.write({
                    'check_out': fields.Datetime.now()
                })

                checkout_count += 1

                membership.message_post(
                    body=_('Forced check-out at %s due to inactive membership status: %s') %
                         (fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'), membership.state),
                    message_type='notification'
                )

        if checkout_count > 0:
            message = _('%s members were automatically checked out due to inactive memberships.') % checkout_count
            notification_type = 'success'
        else:
            message = _('No members needed to be checked out.')
            notification_type = 'info'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': notification_type,
                'sticky': False,
            }
        }

    def _check_and_activate_membership(self):
        """Auto-activate membership when invoice is fully paid"""
        for membership in self:
            if membership.state == 'confirm' and membership.sale_order_id:
                invoices = membership.sale_order_id.invoice_ids.filtered(
                    lambda inv: inv.move_type == 'out_invoice' and inv.state == 'posted'
                )

                if invoices:
                    all_paid = all(inv.payment_state in ('paid', 'in_payment') for inv in invoices)
                    if all_paid:
                        membership.state = "active"
                        membership.message_post(
                            body=_('Membership automatically activated - Payment received'),
                            message_type='notification'
                        )

    @api.depends('sale_order_id.invoice_ids.payment_state', 'sale_order_id.invoice_ids.state')
    def _compute_paid_amount(self):
        for membership in self:
            total_paid = 0.0
            if membership.sale_order_id:
                invoices = membership.sale_order_id.invoice_ids.filtered(
                    lambda inv: inv.move_type == "out_invoice" and inv.state == "posted"
                )
                for invoice in invoices:
                    total_paid += (invoice.amount_total - invoice.amount_residual)

            membership.paid_amount = total_paid

            membership._check_and_activate_membership()

    @api.model
    def _cron_expire_memberships(self):
        """Cron job to automatically set memberships to expired when effective end date passes"""
        today = fields.Date.today()
        _logger.info(f"Starting membership expiry cron job for date: {today}")

        active_memberships = self.search([
            ('state', 'in', ['active', 'paused']),
            ('effective_end_date', '!=', False),
            ('effective_end_date', '<', today)
        ])

        expired_count = 0
        _logger.info(f"Found {len(active_memberships)} memberships to check for expiry")

        for membership in active_memberships:
            try:
                if membership.effective_end_date and membership.effective_end_date < today:
                    _logger.info(
                        f"Expiring membership {membership.reference} - End date: {membership.effective_end_date}")

                    membership._auto_checkout_member("automatic membership expiry")

                    membership.state = 'expired'
                    membership.message_post(
                        body=_('Membership automatically expired on %s (End date: %s)') %
                             (today.strftime('%Y-%m-%d'), membership.effective_end_date.strftime('%Y-%m-%d')),
                        message_type='notification'
                    )
                    expired_count += 1

            except Exception as e:
                _logger.error(f"Error expiring membership {membership.reference}: {str(e)}")
                continue

        _logger.info(f"Cron job completed. Expired {expired_count} memberships")

    @api.depends('membership_date_from', 'membership_date_to')
    def _compute_membership_duration(self):
        for rec in self:
            if rec.membership_date_from and rec.membership_date_to:
                rec.membership_duration = (rec.membership_date_to - rec.membership_date_from).days + 1
            else:
                rec.membership_duration = 0

    def complete_extension(self, days_extended, extension_amount, sale_order_id=None):
        """Complete the extension process and reactivate membership"""
        self.ensure_one()

        if self.state != 'expired':
            raise UserError(_('Only expired memberships can be extended.'))

        if days_extended <= 0:
            raise UserError(_('Days extended must be greater than 0.'))

        extension_record = self.env['gym.membership.extension'].create({
            'membership_id': self.id,
            'extension_date': fields.Date.today(),
            'days_extended': days_extended,
            'extension_amount': extension_amount,
            'sale_order_id': sale_order_id,
            'notes': f'Membership extended by {days_extended} days for ${extension_amount}'
        })

        self.total_extended_days += days_extended
        self.state = 'active'
        self._compute_effective_dates()
        self.message_post(
            body=_('Membership extended by %s days on %s. Amount paid: %s. Membership reactivated. New end date: %s') %
                 (days_extended, fields.Date.today().strftime('%Y-%m-%d'),
                  extension_amount, self.effective_end_date.strftime('%Y-%m-%d')),
            message_type='notification'
        )
        return extension_record

    @api.depends('extension_history_ids')
    def _compute_extension_count(self):
        for rec in self:
            rec.extension_count = len(rec.extension_history_ids)

    @api.depends('state', 'extension_count')
    def _compute_can_extend(self):
        """Compute if membership can be extended"""
        for rec in self:
            max_extensions = 3
            rec.can_extend = (
                    rec.state == 'expired' and
                    rec.extension_count < max_extensions
            )

    def action_check_payment_and_activate(self):
        """Manual button to check payment and activate if paid"""
        self.ensure_one()
        if self.state != 'confirm':
            raise UserError(_('Only confirmed memberships can be activated.'))

        self._check_and_activate_membership()

        if self.state == 'active':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Membership activated successfully!',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Payment not yet received. Please check invoice payment status.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

class GymMembershipPause(models.Model):
    """Model to track pause history"""
    _name = 'gym.membership.pause'
    _description = 'Gym Membership Pause History'
    _order = 'pause_start desc'

    membership_id = fields.Many2one('gym.membership', string='Membership', required=True, ondelete='cascade')
    pause_start = fields.Date(string='Pause Start Date', required=True)
    pause_end = fields.Date(string='Pause End Date', required=True)
    days_paused = fields.Integer(string='Days Paused', required=True)
    notes = fields.Text(string='Notes')


class GymMembershipExtension(models.Model):
    """Model to track extension history"""
    _name = 'gym.membership.extension'
    _description = 'Gym Membership Extension History'
    _order = 'extension_date desc'

    membership_id = fields.Many2one('gym.membership', string='Membership', required=True, ondelete='cascade')
    extension_date = fields.Date(string='Extension Date', required=True, default=fields.Date.today)
    days_extended = fields.Integer(string='Days Extended', required=True)
    extension_amount = fields.Float(string='Extension Amount', required=True)
    sale_order_id = fields.Many2one('sale.order', string='Extension Sale Order')
    notes = fields.Text(string='Notes')