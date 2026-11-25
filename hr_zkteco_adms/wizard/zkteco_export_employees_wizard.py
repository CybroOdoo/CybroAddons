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


class ZktecoExportEmployeesWizard(models.TransientModel):
    """Seed a terminal with employees that already exist in Odoo.

    The usual direction is device -> Odoo. This is the opposite, for a new or
    replaced terminal: it creates the device-user rows and pushes the identity
    fields down. Fingerprints and faces still have to be enrolled at the door.
    """
    _name = 'zkteco.export.employees.wizard'
    _description = 'Export Employees to Device'

    device_id = fields.Many2one(
        'zkteco.device', string='Device', required=True,
        default=lambda self: self._default_device(),
    )
    employee_ids = fields.Many2many(
        'hr.employee', string='Employees', required=True,
        help='Each employee needs a ZKTeco User ID or a Badge ID to become a '
             'PIN on the terminal.',
    )
    overwrite = fields.Boolean(
        string='Overwrite Existing',
        help='Also push employees whose PIN already exists on the terminal.',
    )

    @api.model
    def _default_device(self):
        """Return the default ZKTeco device for the wizard.
                If the wizard is opened from a ZKTeco device, use that device as the
                default. Otherwise, select the first active ZKTeco device."""
        if self.env.context.get('active_model') == 'zkteco.device':
            return self.env.context.get('active_id', False)
        return self.env['zkteco.device'].search([('active', '=', True)], limit=1).id

    def action_export(self):
        """Export selected employees to the selected ZKTeco device.
                Uses the employee's ZKTeco User ID or Badge ID as the device PIN.
                Existing device users are skipped unless overwrite is enabled. Employees
                without a valid PIN are reported as an error."""
        self.ensure_one()
        DeviceUser = self.env['zkteco.device.user']
        pushed = DeviceUser
        skipped = []

        for employee in self.employee_ids:
            pin = employee.zkteco_user_id or employee.barcode
            if not pin:
                skipped.append(employee.name)
                continue
            device_user = DeviceUser.search([
                ('device_id', '=', self.device_id.id),
                ('user_pin', '=', pin),
            ], limit=1)
            if device_user and not self.overwrite:
                continue
            if not device_user:
                device_user = DeviceUser.create({
                    'device_id': self.device_id.id,
                    'user_pin': pin,
                    'name': employee.name,
                    'employee_id': employee.id,
                })
            else:
                device_user.write({'name': employee.name, 'employee_id': employee.id})
            pushed |= device_user

        if skipped:
            raise UserError(_(
                "These employees have neither a ZKTeco User ID nor a Badge ID, "
                "so there is no PIN to create on the terminal:\n\n%s",
                '\n'.join('- %s' % name for name in skipped)))

        pushed.action_push_to_device()
        message = (
            _("%s user(s) sent to the device.", len(pushed))
            if self.device_id.connection_mode == 'tcp'
            else _("%s user(s) queued; the device collects them on its next "
                   "poll.", len(pushed))
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Employees Exported"),
                'message': message,
                'type': 'success' if pushed else 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
