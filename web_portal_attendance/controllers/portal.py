# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: THASNI CP (odoo@cybrosys.com)
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
import pytz
from collections import OrderedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo import http
from odoo.http import request
from odoo.tools import date_utils
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager


class PortalAttendance(portal.CustomerPortal):
    """To get the values of portal attendance"""
    def _prepare_home_portal_values(self, counters):
        """To get the count of the attendance in portal"""
        values = super(PortalAttendance, self)._prepare_home_portal_values(
            counters)
        uid = request.session.uid
        user_id = request.env['res.users'].browse(uid)
        employee_id = request.env['hr.employee'].search(
            [('user_id', '=', user_id.id)])
        attendance_count = request.env['hr.attendance'].search_count(
            [('is_portal', '=', True), ('employee_id', '=', employee_id.id)])
        values.update({
            'attendance_count': attendance_count
        })
        return values

    @http.route('/attendance/checkin', type='http', auth='user', website=True)
    def attendance_checkin(self):
        """When clicking the checkin button it will redirect to the check in
        template"""
        uid = request.session.uid
        user_id = request.env['res.users'].browse(uid)
        employee_id = request.env['hr.employee'].search(
            [('user_id', '=', user_id.id)])
        values = {
            'name': employee_id.name,
            'image': employee_id.image_1920,
            'check_in': datetime.now()
        }
        return request.render("web_portal_attendance.check_in_template", values)

    @http.route('/check/in', type='http', auth='user', website=True)
    def attendance_creation(self):
        """When clicking the checkin button it will create attendance to the
        backend"""
        uid = request.session.uid
        user_id = request.env['res.users'].browse(uid)
        employee_id = request.env['hr.employee'].search(
            [('user_id', '=', user_id.id)])
        attendance = request.env['hr.attendance'].sudo().create({
            'employee_id': employee_id.id,
            'check_in': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'is_portal': True
        })
        check_in = datetime.now()
        user_tz = pytz.timezone(
            request.env.context.get('tz') or request.env.user.tz)
        date_today = pytz.utc.localize(check_in).astimezone(user_tz)
        formatted_time = datetime.strftime(date_today, '%H:%M:%S')
        values = {
            'attendance': attendance,
            'name': employee_id.name,
            'image': employee_id.image_1920,
            'check_out': False,
            'formatted_time': formatted_time,
        }
        return request.render(
            "web_portal_attendance.check_in_welcome_note_template", values)

    @http.route('/check/out', type='http', auth='user', website=True)
    def attendance_checkout(self):
        """When clicking the checkout button it will store the checkout time
        and worked hours in the check in log """
        uid = request.session.uid
        user_id = request.env['res.users'].browse(uid)
        employee_id = request.env['hr.employee'].search(
            [('user_id', '=', user_id.id)])
        values = {
            'name': employee_id.name,
            'image': employee_id.image_1920
        }
        return request.render("web_portal_attendance.check_out_template",
                              values)

    @http.route('/check/out/last', type='http', auth='user', website=True)
    def attendance_final_checkout(self):
        """To display the final checkout template """
        uid = request.session.uid
        user_id = request.env['res.users'].browse(uid)
        employee_id = request.env['hr.employee'].search(
            [('user_id', '=', user_id.id)])
        check_out = datetime.now()
        user_tz = pytz.timezone(
            request.env.context.get('tz') or request.env.user.tz)
        date_today = pytz.utc.localize(check_out).astimezone(user_tz)
        formatted_time = datetime.strftime(date_today, '%H:%M:%S')
        attendance = request.env['hr.attendance'].search(
            [('employee_id', '=', employee_id.id), ('check_out', '=', False),
             ('is_portal', '=', True)],
            order="check_in desc", limit=1)
        # If there is an attendance record with no check-out time,
        # update it with the current time
        if attendance:
            check_out = datetime.now()
            check_in = attendance.check_in
            worked_hours = check_out - check_in
            total_seconds = worked_hours.total_seconds()
            hours = int(total_seconds / 3600)
            minutes = int((total_seconds % 3600) / 60)
            worked_hours_str = "{:02d}:{:02d}".format(hours, minutes)
            hours, minutes = map(int, worked_hours_str.split(':'))
            worked_hours_float = hours + minutes / 60.0
            attendance.write({
                'check_out': check_out.strftime('%Y-%m-%d %H:%M:%S'),
                'worked_hours': worked_hours_float
            })
        values = {
            'name': employee_id.name,
            'image': employee_id.image_1920,
            'formatted_time': formatted_time
        }
        return request.render("web_portal_attendance.portal_last_checkout",
                              values)

    @http.route(['/attendance/list', '/attendance/list/page/<int:page>'],
                type='http', website=True)
    def attendance_search_sort_view(self, page=1, search=None,
                                    search_in="Check In",
                                    filterby="all", **kwargs):
        """To search and filter in the list view of attendance"""
        uid = request.session.uid
        user_id = request.env['res.users'].browse(uid)
        employee_id = request.env['hr.employee'].search(
            [('user_id', '=', user_id.id)])
        search_list = {
            'Work Hour': {'label': 'Work Hour', 'input': 'Work Hour',
                          'domain': [('worked_hours', 'ilike', search)]},
            'Check In': {'label': 'Check In', 'input': 'Check In',
                         'domain': [('check_in', 'ilike', search)]},
            'Check Out': {'label': 'Check Out', 'input': 'Check Out',
                          'domain': [('check_out', 'ilike', search)]}, }
        today = fields.Date.today()
        last_week = today + relativedelta(weeks=-1)
        last_month = today + relativedelta(months=-1)
        last_year = today + relativedelta(years=-1)
        searchbar_filters = {
            'all': {'label': 'All', 'domain': []},
            'today': {
                'label': 'Today',
                'domain': [("check_in", ">=",
                            fields.Datetime.to_string(fields.Datetime.today())),
                           ("check_in", "<=", fields.Datetime.to_string(
                               fields.Datetime.today().replace(hour=23,
                                                               minute=59,
                                                               second=59)))]},
            'week': {
                'label': 'Last Week',
                'domain': [
                    ('check_in', '>=', date_utils.start_of(last_week, "week")),
                    ('check_in', '<=', date_utils.end_of(last_week, 'week'))]},
            'month': {
                'label': 'Last Month',
                'domain': [('check_in', '>=',
                            date_utils.start_of(last_month, 'month')),
                           ('check_in', '<=',
                            date_utils.end_of(last_month, 'month'))]},
            'year': {
                'label': 'Last Year',
                'domain': [
                    ('check_in', '>=', date_utils.start_of(last_year, 'year')),
                    ('check_in', '<=', date_utils.end_of(last_year, 'year'))]}}
        search_domain = search_list[search_in]['domain']
        filter_domain = searchbar_filters[filterby]['domain']
        attendance_obj = request.env['hr.attendance'].search(
            [('is_portal', '=', True), ('employee_id', '=', employee_id.id)])
        total_attendance = attendance_obj.search_count(
            [('is_portal', '=', True),
             ('employee_id', '=',
              employee_id.id)] + search_domain + filter_domain)
        page_detail = pager(url='/attendance/list',
                            total=total_attendance,
                            page=page,
                            step=10,
                            url_args={'search': search,
                                      'search_in': search_in,
                                      'filterby': filterby})
        attendance_domain = [('is_portal', '=', True),
                             ('employee_id', '=', employee_id.id)]
        if search_domain:
            attendance_domain += search_domain
        if filter_domain:
            attendance_domain += filter_domain
        attendance = attendance_obj.search(
            attendance_domain,
            limit=10,
            offset=page_detail['offset'])
        vals = {
            'attendance': attendance,
            'page_name': 'attendance',
            'pager': page_detail,
            'search': search,
            'search_in': search_in,
            'searchbar_inputs': search_list,
            'default_url': '/attendance/list',
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        }
        return request.render(
            "web_portal_attendance.portal_list_attendance_order", vals)
