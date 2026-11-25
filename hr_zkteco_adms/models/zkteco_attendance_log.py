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
import logging
from datetime import timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

# ZKTeco ATTLOG status (check type) codes.
CHECK_IN_CODES = {'0', '3', '4'}    # check-in, break-in, overtime-in
CHECK_OUT_CODES = {'1', '2', '5'}   # check-out, break-out, overtime-out

VERIFY_MODES = {
    '0': 'Password',
    '1': 'Fingerprint',
    '2': 'Card',
    '3': 'Password',
    '4': 'Card',
    '15': 'Face',
    '16': 'Fingerprint + Password',
    '25': 'Palm',
}


class ZktecoAttendanceLog(models.Model):
    _name = 'zkteco.attendance.log'
    _description = 'ZKTeco Raw Punch Log'
    _order = 'punch_time desc, id desc'
    _rec_name = 'device_user_id'

    device_id = fields.Many2one(
        'zkteco.device', required=True, ondelete='cascade', index=True,
    )
    company_id = fields.Many2one(
        related='device_id.company_id', store=True, readonly=True,
    )
    device_user_id = fields.Char(
        string='Device User ID', required=True, index=True,
        help='User PIN on the biometric device.',
    )
    punch_time = fields.Datetime(required=True, index=True)
    status = fields.Char(
        string='Check Type',
        help='Raw check type sent by the device: 0/3/4 in, 1/2/5 out, '
             '255 device decides.',
    )
    verify_mode = fields.Char(
        help='How the user authenticated on the device '
             '(1=fingerprint, 15=face, 2=card, ...).',
    )
    verify_mode_label = fields.Char(
        string='Verified By', compute='_compute_verify_mode_label',
    )
    employee_id = fields.Many2one('hr.employee', index=True, readonly=True)
    attendance_id = fields.Many2one('hr.attendance', readonly=True, ondelete='set null')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('done', 'Processed'),
        ('unmapped', 'Unmapped User'),
        ('error', 'Error'),
    ], default='pending', required=True, index=True)
    error_message = fields.Char(readonly=True)

    _punch_uniq = models.Constraint(
        'unique (device_id, device_user_id, punch_time)',
        'This punch has already been recorded.',
    )

    status_code_id = fields.Many2one(
        'zkteco.status.code', string='Status', compute='_compute_status_code')
    status_label = fields.Char(compute='_compute_status_code')
    status_color = fields.Char(compute='_compute_status_code')

    @api.depends('verify_mode')
    def _compute_verify_mode_label(self):
        """Compute the human-readable label for the attendance verification mode."""
        for log in self:
            log.verify_mode_label = VERIFY_MODES.get(log.verify_mode, log.verify_mode or '')

    @api.depends('status', 'company_id')
    def _compute_status_code(self):
        """Compute the status code, label, and color for each attendance log.
                The status code mapping is loaded per company and reused for all logs
                belonging to the same company. If no matching status code is found,
                the original status is used as the label and ``muted`` is used as
                the default color."""
        StatusCode = self.env['zkteco.status.code']
        maps = {}
        for log in self:
            company = log.company_id
            if company.id not in maps:
                maps[company.id] = StatusCode._get_map(company)
            code = maps[company.id].get((log.status or '').strip())
            log.status_code_id = code
            log.status_label = code.name if code else (log.status or '')
            log.status_color = code.color if code else 'muted'

    # -------------------------------------------------------------
    # Creation with deduplication
    # -------------------------------------------------------------
    @api.model
    def _create_deduplicated(self, vals_list):
        """Create logs, silently skipping punches already recorded.
        Devices retransmit their whole log on 'DATA QUERY ATTLOG' and after
        communication errors, so duplicates are the normal case, not the
        exception. Only the punch window covered by this payload is loaded
        for comparison - a device that has been running for a year must not
        drag its whole history into memory on every push.
        """
        if not vals_list:
            return self.browse()
        device_ids = {vals['device_id'] for vals in vals_list}
        times = [vals['punch_time'] for vals in vals_list]
        existing = {
            (log.device_id.id, log.device_user_id, log.punch_time)
            for log in self.search([
                ('device_id', 'in', list(device_ids)),
                ('punch_time', '>=', min(times) - timedelta(seconds=1)),
                ('punch_time', '<=', max(times) + timedelta(seconds=1)),
            ])
        }
        to_create = []
        seen = set()
        for vals in vals_list:
            key = (vals['device_id'], vals['device_user_id'], vals['punch_time'])
            if key in existing or key in seen:
                continue
            seen.add(key)
            to_create.append(vals)
        records = self.create(to_create)
        records._process()
        return records

    # -------------------------------------------------------------
    # Processing into hr.attendance
    # -------------------------------------------------------------
    def _employee_map(self):
        """Resolve employees for the whole batch in a fixed number of queries.

        Returns {(device_id, device_user_id): employee}. Resolution order is
        the explicit mapping on the device user list, then the dedicated
        ZKTeco user id on the employee, then the badge id.
        """
        if not self:
            return {}
        Employee = self.env['hr.employee'].sudo()
        keys = {(log.device_id.id, log.device_user_id) for log in self}
        pins = sorted({pin for _device_id, pin in keys})

        mapping = {}
        device_users = self.env['zkteco.device.user'].sudo().search([
            ('device_id', 'in', self.device_id.ids),
            ('user_pin', 'in', pins),
            ('employee_id', '!=', False),
        ])
        for device_user in device_users:
            mapping[(device_user.device_id.id, device_user.user_pin)] = device_user.employee_id

        missing = keys - set(mapping)
        if not missing:
            return mapping

        # Fall back to the employee record itself: dedicated ZKTeco id first,
        # badge id second, each restricted to the device's company.
        indexes = []
        for field_name in ('zkteco_user_id', 'barcode'):
            index = {}
            for employee in Employee.search([(field_name, 'in', pins)], order='id'):
                index.setdefault((employee.company_id.id, employee[field_name]), employee)
            indexes.append(index)

        companies = {log.device_id.id: log.company_id.id for log in self}
        for device_id, pin in missing:
            company_id = companies.get(device_id)
            for index in indexes:
                employee = index.get((company_id, pin))
                if not employee and not company_id:
                    # Device with no company: accept the pin only when a
                    # single employee across all companies claims it.
                    matches = [emp for (_company, key), emp in index.items() if key == pin]
                    employee = matches[0] if len(matches) == 1 else None
                if employee:
                    mapping[(device_id, pin)] = employee
                    break
        return mapping

    def _find_employee(self):
        """Resolve the employee for a single punch."""
        self.ensure_one()
        return self._employee_map().get(
            (self.device_id.id, self.device_user_id), self.env['hr.employee']
        )

    def action_process(self):
        """Process the selected attendance records."""
        self._process()

    def _process(self):
        """Turn raw punches into hr.attendance records.

        Punches are handled per employee in chronological order. Explicit
        check types are honoured; unknown types (255) alternate: close the
        open attendance if there is one, otherwise open a new one. Each punch
        is processed in its own savepoint so a bad one cannot block the batch.
        """
        todo = self.filtered(lambda log: log.state in ('pending', 'unmapped', 'error'))
        if not todo:
            return
        Attendance = self.env['hr.attendance'].sudo()
        employees = todo._employee_map()
        for log in todo.sorted(key=lambda log: (log.device_user_id, log.punch_time)):
            employee = employees.get((log.device_id.id, log.device_user_id))
            if not employee:
                log.write({'state': 'unmapped', 'error_message': False})
                continue
            try:
                with self.env.cr.savepoint():
                    log._process_one(Attendance, employee)
            except Exception as exc:  # noqa: BLE001 - any ORM/validation error
                _logger.info("ZKTeco log %s: processing failed: %s", log.id, exc)
                log.write({'state': 'error', 'error_message': str(exc)[:512]})

    def _punch_direction(self, open_attendance):
        """Decide whether this punch opens or closes an attendance.

        The configured status-code table wins; codes it does not list fall
        back to the firmware defaults. The device's Check Option overrides
        both, because a single-door reader physically cannot report the
        direction it was not installed for.
        """
        self.ensure_one()
        status = (self.status or '255').strip()
        check_option = self.device_id.check_option
        if check_option == 'in':
            return 'in'
        if check_option == 'out':
            return 'out'

        configured = self.env['zkteco.status.code']._get_map(self.company_id).get(status)
        punch_type = configured.punch_type if configured else None
        if punch_type in ('in', 'out', 'ignore'):
            return punch_type
        if punch_type is None:
            if status in CHECK_IN_CODES:
                return 'in'
            if status in CHECK_OUT_CODES:
                return 'out'
        # 'auto', or an unknown code: alternate on the open attendance.
        return 'out' if open_attendance else 'in'

    def _process_one(self, Attendance, employee):
        """Process a single attendance log for the specified employee.
                Determines whether the biometric punch represents a check-in or
                check-out, updates an existing open attendance record when applicable,
                or creates a new attendance record for a check-in. Invalid or
                inconsistent punches are marked as errors."""
        self.ensure_one()
        open_attendance = Attendance.search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], order='check_in desc', limit=1)
        values = {'employee_id': employee.id, 'state': 'done', 'error_message': False}

        direction = self._punch_direction(open_attendance)
        if direction == 'ignore':
            values['attendance_id'] = False
            self.write(values)
            return

        is_out = direction == 'out'
        if is_out and open_attendance:
            if self.punch_time <= open_attendance.check_in:
                # Late-arriving duplicate or clock skew: nothing sensible to do.
                values.update(state='error',
                              error_message=_('Check-out before the open check-in.'))
                self.write(values)
                return
            open_attendance.write({'check_out': self.punch_time,
                                   'out_mode': 'biometric'})
            values['attendance_id'] = open_attendance.id
        elif is_out:
            values.update(state='error',
                          error_message=_('Check-out punch without an open check-in.'))
        else:
            attendance = Attendance.create({
                'employee_id': employee.id,
                'check_in': self.punch_time,
                'in_mode': 'biometric',
            })
            values['attendance_id'] = attendance.id
        self.write(values)

    @api.model
    def _cron_process_pending(self):
        """Process pending and unmapped ZKTeco attendance logs.
                Retrieves up to 2,000 pending or unmapped attendance logs in
                chronological order and processes them to create or update the
                corresponding HR attendance records."""
        logs = self.search([('state', 'in', ('pending', 'unmapped'))],
                           order='punch_time asc', limit=2000)
        logs._process()
