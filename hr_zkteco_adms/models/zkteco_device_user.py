# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ZktecoDeviceUser(models.Model):
    _name = 'zkteco.device.user'
    _description = 'ZKTeco Device User'
    _order = 'device_id, user_pin'
    _rec_name = 'display_label'

    device_id = fields.Many2one(
        'zkteco.device', required=True, ondelete='cascade', index=True,
    )
    company_id = fields.Many2one(
        related='device_id.company_id', store=True, readonly=True,
    )
    user_pin = fields.Char(string='Device User ID', required=True, index=True)
    device_uid = fields.Integer(
        string='Internal UID', readonly=True,
        help="The terminal's own row index for this user. Only meaningful in "
             "Direct IP mode, where it must be reused when updating a user.",
    )
    name = fields.Char(string='Name on Device')
    card = fields.Char(string='Card Number')
    privilege = fields.Char()
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', index=True,
        help='Employee whose attendance is recorded for this device user.',
    )
    display_label = fields.Char(compute='_compute_display_label')
    punch_count = fields.Integer(compute='_compute_punch_count')
    last_punch = fields.Datetime(compute='_compute_punch_count')

    _pin_uniq = models.Constraint(
        'unique (device_id, user_pin)',
        'This user already exists on this device.',
    )

    @api.depends('user_pin', 'name')
    def _compute_display_label(self):
        """Compute the display label for the device user.
                Combines the user's PIN and name when a name is available. If no name
                is set, the user's PIN is used as the display label."""
        for user in self:
            user.display_label = f"{user.user_pin} - {user.name}" if user.name else (user.user_pin or '')

    def _compute_punch_count(self):
        """Compute the punch count and latest punch time for each device user.
                Groups attendance logs by device and user PIN to efficiently calculate
                the total number of punches and the most recent punch time for each
                device user."""
        Log = self.env['zkteco.attendance.log']
        groups = Log._read_group(
            [('device_id', 'in', self.device_id.ids),
             ('device_user_id', 'in', self.mapped('user_pin'))],
            ['device_id', 'device_user_id'], ['__count', 'punch_time:max'],
        )
        data = {
            (device.id, pin): (count, last)
            for device, pin, count, last in groups
        }
        for user in self:
            count, last = data.get((user.device_id.id, user.user_pin), (0, False))
            user.punch_count = count
            user.last_punch = last

    @api.model
    def _register_from_device(self, device, pin, values):
        """Create or update a device user from an OPERLOG USER line."""
        user = self.search([
            ('device_id', '=', device.id), ('user_pin', '=', pin),
        ], limit=1)
        vals = {
            'name': values.get('name') or (user.name if user else False),
            'card': values.get('card') or (user.card if user else False),
            'privilege': values.get('pri') or (user.privilege if user else False),
        }
        if str(values.get('uid') or '').isdigit():
            vals['device_uid'] = int(values['uid'])
        if user:
            user.write(vals)
            return user
        vals.update(device_id=device.id, user_pin=pin)
        user = self.create(vals)
        user._auto_map_employee()
        return user

    def _auto_map_employee(self):
        """Automatically map device users to their corresponding employees.
                Searches for an employee using the ZKTeco user PIN first and falls back
                to the employee barcode when no match is found. Only users without an
                existing employee mapping are processed, and the search is restricted
                to the user's company when applicable."""
        Employee = self.env['hr.employee'].sudo()
        for user in self.filtered(lambda u: not u.employee_id):
            domain_company = [('company_id', 'in', [user.company_id.id, False])] \
                if user.company_id else []
            employee = Employee.search(
                [('zkteco_user_id', '=', user.user_pin)] + domain_company, limit=1)
            if not employee:
                employee = Employee.search(
                    [('barcode', '=', user.user_pin)] + domain_company, limit=1)
            if employee:
                user.employee_id = employee

    def action_auto_map(self):
        """Retry automatic mapping on the selected users."""
        self._auto_map_employee()

    def action_view_punches(self):
        """Open the punch logs associated with the device user.
                Returns an Odoo window action displaying the attendance punch logs
                recorded for the selected device user on the corresponding device.
                :return: Odoo window action for viewing the user's punch logs."""
        self.ensure_one()
        return {
            'name': _('Punch Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'zkteco.attendance.log',
            'view_mode': 'list,form',
            'domain': [('device_id', '=', self.device_id.id),
                       ('device_user_id', '=', self.user_pin)],
        }

    # -------------------------------------------------------------
    # Pushing back to the device
    # -------------------------------------------------------------
    def action_push_to_device(self):
        """Send these users to the terminal, whichever transport it uses.

        Only the identity fields travel; fingerprint and face templates are
        enrolled on the terminal itself and are never sent from Odoo.
        """
        for user in self:
            device = user.device_id
            if device.connection_mode == 'tcp':
                # Applied immediately, so a failure is reported to the user.
                device._tcp_set_user(user)
                continue
            if not device.active:
                raise UserError(_(
                    "Device %s is not approved yet and will not poll for "
                    "commands.", device.display_name))
            name = (user.employee_id.name or user.name or '')[:24]
            device._queue_command(
                'DATA UPDATE USERINFO PIN={pin}\tName={name}\tPri={pri}\t'
                'Passwd=\tCard={card}\tGrp=1\tTZ=0000000000000000'.format(
                    pin=user.user_pin, name=name,
                    pri=user.privilege or '0', card=user.card or '',
                )
            )

    def action_delete_from_device(self):
        """Delete the selected users from their ZKTeco devices.
                Uses Direct IP mode to delete users immediately when the device is
                configured for TCP communication. For ADMS devices, queues a command
                for the device to process when it next polls the server. Inactive
                ADMS devices are rejected because they cannot process queued commands."""
        for user in self:
            device = user.device_id
            if device.connection_mode == 'tcp':
                device._tcp_delete_user(user)
                continue
            if not device.active:
                raise UserError(_(
                    "Device %s is not approved yet and will not poll for "
                    "commands.", device.display_name))
            device._queue_command(f'DATA DELETE USERINFO PIN={user.user_pin}')

    # -------------------------------------------------------------
    # Overrides
    # -------------------------------------------------------------
    def write(self, vals):
        """Update the device user and process newly mapped attendance logs.
                After an employee is assigned to a device user, reprocesses the user's
                previously unmapped or errored attendance logs so that the queued punches
                can be associated with the mapped employee.
                :param vals: Values to update on the device user records.
                :return: Result of the parent ``write`` method."""
        res = super().write(vals)
        if vals.get('employee_id'):
            # Mapping an employee unlocks their queued punches.
            for user in self:
                self.env['zkteco.attendance.log'].sudo().search([
                    ('device_id', '=', user.device_id.id),
                    ('device_user_id', '=', user.user_pin),
                    ('state', 'in', ('unmapped', 'error')),
                ])._process()
        return res
