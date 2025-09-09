# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
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
        for record in self:
            record.state = 'checked_out' if record.check_out else 'checked_in'

    @api.depends('check_in', 'check_out')
    def _compute_duration(self):
        for record in self:
            if record.check_in and record.check_out:
                delta = record.check_out - record.check_in
                record.duration = delta.total_seconds() / 3600
            else:
                record.duration = 0.0

    @api.model
    def create(self, vals):
        """Override create to validate BEFORE creating the record"""
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

        return super(GymAttendance, self).create(vals)

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
        """Check in a member - simplified since validation is now in create()"""
        self.ensure_one()

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
        """Validate if member can check in - returns dict with can_checkin boolean and message"""

        active_memberships = self.env['gym.membership'].search([
            ('member_id', '=', member.id),
            ('state', '=', 'active')
        ])

        active_membership = None
        if active_memberships:
            if len(active_memberships) == 1:
                active_membership = active_memberships
            else:
                active_membership = max(active_memberships,
                                        key=lambda m: m.effective_end_date or fields.Date.today())

        if active_membership:
            if active_membership.effective_end_date and active_membership.effective_end_date < fields.Date.today():
                active_membership.action_expire()
            else:
                return {
                    'can_checkin': True,
                    'message': _('Check-in allowed.')
                }

        any_membership = self.env['gym.membership'].search([
            ('member_id', '=', member.id)
        ], order='id desc', limit=1)

        if not any_membership:
            return {
                'can_checkin': False,
                'message': _('No membership found for this member.')
            }

        if any_membership.state == 'paused':
            return {
                'can_checkin': False,
                'message': _(
                    'Cannot check in. Your latest membership is PAUSED.\n'
                    'Please resume your membership to check in.'
                )
            }
        elif any_membership.state == 'expired':
            return {
                'can_checkin': False,
                'message': _(
                    'Cannot check in. Your latest membership has EXPIRED.\n'
                    'Please renew your membership to continue.'
                )
            }
        elif any_membership.state in ['draft', 'confirm']:
            return {
                'can_checkin': False,
                'message': _(
                    'Cannot check in. Your membership is not yet active.\n'
                    'Please wait for activation or contact support.'
                )
            }
        else:
            return {
                'can_checkin': False,
                'message': _(
                    'Cannot check in. Membership status: %s'
                ) % any_membership.state.title()
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

        attendance = self.create({
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