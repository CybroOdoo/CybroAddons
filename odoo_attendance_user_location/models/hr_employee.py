# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreenath K, Shafna K (odoo@cybrosys.com)
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
from geopy.geocoders import Nominatim
from odoo import exceptions, fields, models, _


class HrEmployee(models.AbstractModel):
    """Inherits HR Employee model"""
    _inherit = 'hr.employee'

    def attendance_manual(self, next_action, entered_pin=None):
        """Override this method to add latitude and longitude"""
        self.ensure_one()

        latitudes = self.env.context.get('latitude', False)
        longitudes = self.env.context.get('longitude', False)
        self.ensure_one()
        attendance_user_and_no_pin = self.user_has_groups('hr_attendance.group_hr_attendance_user,'
                                                          '!hr_attendance.group_hr_attendance_use_pin')
        can_check_without_pin = attendance_user_and_no_pin or self.user_id == self.env.user and entered_pin is None

        if can_check_without_pin or entered_pin is not None and entered_pin == self.sudo().pin:
            return self._attendance_action(latitudes, longitudes,
                                           next_action)
        if not self.user_has_groups('hr_attendance.group_hr_attendance_user'):
            return {'warning': _('To activate Kiosk mode without pin code, you '
                                 'must have access right as an Officer or above'
                                 'in the Attendance app. Please contact your '
                                 'administrator.')}
        return {'warning': _('Wrong PIN')}

    def _attendance_action(self, latitudes, longitudes, next_action):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should
            return to. ("My Attendances" or "Kiosk Mode")
        """
        self.ensure_one()
        employee = self.sudo()
        action_message = self.env['ir.actions.actions']._for_xml_id('hr_attendance.'
                                                                    'hr_attendance_action_greeting_message')

        action_message['previous_attendance_change_date'] = employee.last_attendance_id and (
                employee.last_attendance_id.check_out
                or employee.last_attendance_id.check_in) or False
        action_message['employee_name'] = employee.name
        action_message['barcode'] = employee.barcode
        action_message['next_action'] = next_action
        action_message['hours_today'] = employee.hours_today
        action_message['kiosk_delay'] = \
            employee.company_id.attendance_kiosk_delay * 1000
        if employee.user_id:
            modified_attendance = employee.with_user(employee.user_id).sudo()._attendance_action_change(longitudes,
                                                                                                        latitudes)
        else:
            modified_attendance = employee._attendance_action_change(longitudes,
                                                                     latitudes)
        action_message['attendance'] = modified_attendance.read()[0]
        action_message['total_overtime'] = employee.total_overtime

        # Overtime have a unique constraint on the day, no need for limit=1

        action_message['overtime_today'] = \
            self.env['hr.attendance.overtime'].sudo().search([('employee_id', '=', employee.id),
                                                              ('date', '=', fields.Date.context_today(self)),
                                                              ('adjustment', '=', False)]).duration or 0
        return {'action': action_message}

    def _attendance_action_change(self, longitudes, latitudes):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        self.ensure_one()
        action_date = fields.Datetime.now()
        # create a geolocator object
        geolocator = Nominatim(user_agent='my-app')
        # get the location using the geolocator object
        location = geolocator.reverse(str(latitudes) + ', ' + str(longitudes))
        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'checkin_address': location.address,
                'checkin_latitude': latitudes,
                'checkin_longitude': longitudes,
                'checkin_location': 'https://www.google.com/maps/place/' + location.address,
            }
            return self.env['hr.attendance'].create(vals)
        attendance = self.env['hr.attendance'].search(
            [('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
        if attendance:
            attendance.write({
                'checkout_address': location.address,
                'checkout_latitude': latitudes,
                'checkout_longitude': longitudes,
                'checkout_location': 'https://www.google.com/maps/place/'
                                     + location.address,
            })
            attendance.check_out = action_date
        else:
            raise exceptions.UserError(_('Cannot perform check out on '
                                         '%(empl_name)s, could not find corresponding check in.'
                                         ' Your attendances have probably been modified manually by'
                                         ' human resources.') % {
                                           'empl_name': self.sudo().name})
        return attendance
