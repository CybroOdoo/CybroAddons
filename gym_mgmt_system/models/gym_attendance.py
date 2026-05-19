# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models
from odoo.tools import _
from odoo.exceptions import UserError


class GymAttendance(models.Model):
    """Simple Gym Attendance Model"""
    _name = 'gym.attendance'
    _description = 'Gym Attendance'
    _order = 'check_in desc'
    _rec_name = 'member_id'

    member_id = fields.Many2one('res.partner', string='Member', required=True,
                                domain="[('is_gym_member', '=', True)]")
    check_in = fields.Datetime(string='Check In', required=True,
                               default=fields.Datetime.now)
    check_out = fields.Datetime(string='Check Out')

    duration = fields.Float(string='Duration (Hours)',
                            compute='_compute_duration', store=True)

    state = fields.Selection([
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out')
    ], string='State', compute='_compute_state', store=True)

    @api.depends('check_out')
    def _compute_state(self):
        """Set state based on check-out status."""
        for record in self:
            record.state = 'checked_out' if record.check_out else 'checked_in'

    @api.depends('check_in', 'check_out')
    def _compute_duration(self):
        """Compute duration in hours between check-in and check-out."""
        for record in self:
            if record.check_in and record.check_out:
                delta = record.check_out - record.check_in
                record.duration = delta.total_seconds() / 3600
            else:
                record.duration = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to validate BEFORE creating the record"""
        for vals in vals_list:
            if 'member_id' in vals:
                member_id = vals['member_id']
                existing_checkin = self.search([
                    ('member_id', '=', member_id),
                    ('check_out', '=', False)
                ])

                if existing_checkin:
                    member_name = self.env['res.partner'].browse(member_id).name
                    raise UserError(_('%s is already checked in at %s. Please check out first.') %
                                    (member_name, existing_checkin.check_in.strftime('%Y-%m-%d %H:%M:%S')))
                member = self.env['res.partner'].browse(member_id)
                validation = self._validate_member_can_checkin(member)
                if not validation['can_checkin']:
                    raise UserError(validation['message'])

        return super(GymAttendance, self).create(vals_list)

    def write(self, vals):
        """Override write to validate member changes"""
        if 'member_id' in vals:
            existing_checkin = self.env['gym.attendance'].search([
                ('member_id', '=', vals['member_id']),
                ('check_out', '=', False),
                ('id', 'not in', self.ids)
            ])
            if existing_checkin:
                member_name = self.env['res.partner'].browse(vals['member_id']).name
                raise UserError(_('%s is already checked in. Cannot change to this member.') % member_name)

        return super(GymAttendance, self).write(vals)

    def action_check_in(self):
        """Check in a member - validate membership before allowing manual check-in"""
        self.ensure_one()

        validation = self._validate_member_can_checkin(self.member_id)
        if not validation['can_checkin']:
            raise UserError(validation['message'])
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Welcome {self.member_id.name}! Check-in successful.',
                'type': 'success',
                'sticky': False,
            }
        }

    def _validate_member_can_checkin(self, member):
        """Validate if member can check in - returns dict with can_checkin boolean and message.
        Also expires any active membership whose effective_end_date is in the past.
        """
        Membership = self.env['gym.membership'].sudo()
        memberships = Membership.search([('member_id', '=', member.id)], order='id desc')

        if not memberships:
            return {
                'can_checkin': False,
                'message': _('No membership found for this member.')
            }
        today = fields.Date.today()
        for m in memberships:
            try:
                if m.state == 'active' and m.effective_end_date:
                    if m.effective_end_date < today:
                        try:
                            m.sudo().action_expire()
                        except Exception:
                            try:
                                m.sudo().write({'state': 'expired'})
                            except Exception:
                                pass
            except Exception:
                pass

        active = Membership.search([('member_id', '=', member.id), ('state', '=', 'active')],
                                   order='id desc', limit=1)
        if active:
            if active.effective_end_date and active.effective_end_date < today:
                try:
                    active.sudo().action_expire()
                except Exception:
                    try:
                        active.sudo().write({'state': 'expired'})
                    except Exception:
                        pass
                return {
                    'can_checkin': False,
                    'message': _('Cannot check in. Your membership has EXPIRED.')
                }
            return {
                'can_checkin': True,
                'message': _('Check-in allowed.')
            }

        latest_membership = Membership.search([('member_id', '=', member.id)], order='id desc', limit=1)

        state_messages = {
            'paused': _('Cannot check in. Your latest membership is PAUSED.'),
            'expired': _('Cannot check in. Your latest membership has EXPIRED.'),
            'draft': _('Cannot check in. Your membership is not yet active.'),
            'confirm': _('Cannot check in. Your membership is not yet active.'),
            'cancelled': _('Cannot check in. Your membership is CANCELLED.')
        }

        return {
            'can_checkin': False,
            'message': state_messages.get(latest_membership.state,
                                          _('Cannot check in. Membership status: %s') %
                                          latest_membership.state.title())
        }

    def action_check_out(self):
        """Check out manually"""
        self.ensure_one()
        if self.check_out:
            raise UserError(_('Already checked out.'))
        self.check_out = fields.Datetime.now()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Goodbye {self.member_id.name}! Duration: {self.duration:.2f} hours',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def quick_checkin(self, member_id):
        """Method for quick check-in from external calls"""
        member = self.env['res.partner'].browse(member_id)
        if not member.exists():
            raise UserError(_('Member not found.'))
        self.create({
            'member_id': member_id,
            'check_in': fields.Datetime.now(),
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Welcome {member.name}! Check-in successful.',
                'type': 'success',
                'sticky': False,
            }
        }
