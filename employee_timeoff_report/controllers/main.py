# -*- coding: utf-8 -*-
#############################################################################
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
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import random
import datetime
import logging
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class TimeoffReportController(http.Controller):
    """Controller for handling employee time off report and verification."""

    @http.route('/my/timeoff/send_otp', type='json', auth="public", website=True, csrf=False)
    def send_otp(self, email):
        """Generates and sends an OTP to the employee work email."""
        employee = request.env['hr.employee'].sudo().search([
            ('work_email', '=', email)
        ], limit=1)
        
        if not employee:
            return {
                'success': False,
                'message': 'No employee found with this email address.'
            }
        
        otp = str(random.randint(100000, 999999))
        # Store OTP in session for verification
        request.session['timeoff_otp'] = otp
        request.session['timeoff_email'] = email
        
        # Send mail logic (using Odoo mail templates for premium feel)
        company = request.env.company
        mail_values = {
            'subject': 'Time Off Access OTP',
            'email_to': email,
            'email_from': company.email or company.partner_id.email or 'noreply@example.com',
            'body_html': f'<div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 10px;">'
                         f'<h2 style="color: #1e3a8a;">Access Verification</h2>'
                         f'<p>Hello,</p>'
                         f'<p>You requested access to your Time Off report. Please use the following One-Time Password (OTP) to verify your identity:</p>'
                         f'<div style="font-size: 24px; font-weight: bold; color: #3b82f6; background: #f0f7ff; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">'
                         f'{otp}'
                         f'</div>'
                         f'<p>This code will expire shortly. If you did not request this code, please ignore this email.</p>'
                         f'<p style="color: #777; font-size: 12px; margin-top: 30px;">Sent by {company.name}</p>'
                         f'</div>',
        }
        _logger.info("Sending Time Off Access OTP to %s for employee %s", email, employee.name)
        request.env['mail.mail'].sudo().create(mail_values).send(auto_commit=True)
        
        return {'success': True}

    @http.route('/my/timeoff/authenticate', type='json', auth="public", website=True, csrf=False)
    def authenticate(self, otp):
        """Verifies the provided OTP and marks the session as authenticated."""
        stored_otp = request.session.get('timeoff_otp')
        if stored_otp and otp == stored_otp:
            request.session['timeoff_authenticated'] = True
            return {'success': True}
        return {'success': False, 'message': 'Invalid OTP.'}

    @http.route('/my/timeoff/success', type='http', auth="public", website=True)
    def my_timeoff_success(self, **kwargs):
        """Renders the authentication wizard page."""
        if not request.session.get('timeoff_authenticated'):
            return request.redirect('/my/timeoff')

        email = request.session.get('timeoff_email')
        employee = request.env['hr.employee'].sudo().search([
            ('work_email', '=', email)
        ], limit=1)

        if not employee:
            request.session['timeoff_authenticated'] = False
            return request.redirect('/my/timeoff/login')

        # Fetch all leaves for the employee
        timeoffs = request.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', 'not in', ('cancel', 'refuse'))
        ], order='date_from desc')

        # Fetch leave summary data
        leave_types = request.env['hr.leave.type'].sudo().search([])
        leave_summary = []
        # Odoo 16 uses get_employees_days
        summary_data = leave_types.get_employees_days(
            [employee.id])[employee.id]

        for lt in leave_types:
            stats = summary_data.get(lt.id, {})
            if stats.get('max_leaves', 0) > 0:
                leave_summary.append({
                    'name': lt.name,
                    'allocated': stats.get('max_leaves', 0),
                    'taken': stats.get('leaves_taken', 0),
                    'remaining': stats.get('remaining_leaves', 0),
                })

        if not timeoffs and not leave_summary:
            request.session['timeoff_authenticated'] = False
            request.session['timeoff_email'] = False
            return request.redirect('/my/timeoff/no_data')

        return request.render('employee_timeoff_report.timeoff_report_template', {
            'employee': employee,
            'timeoffs': timeoffs,
            'leave_summary': leave_summary,
        })

    @http.route('/my/timeoff/no_data', type='http', auth="public", website=True)
    def my_timeoff_no_data(self, **kwargs):
        """Renders the 'No Data' error page."""
        return request.render('employee_timeoff_report.timeoff_no_data_template')

    @http.route('/my/timeoff', type='http', auth="public", website=True)
    def my_timeoff(self, **kwargs):
        """Renders the time off report dashboard."""
        # Redirect to login if not authenticated
        request.session['timeoff_authenticated'] = False
        request.session['timeoff_email'] = False

        employee = request.env['hr.employee']
        if not request.env.user._is_public():
            employee = request.env.user.employee_id

        return request.render('employee_timeoff_report.timeoff_auth_page_template', {
            'employee': employee,
        })
        

    @http.route('/my/timeoff/print', type='http', auth="public", website=True)
    def print_timeoff_report(self, **kwargs):
        """Generates and returns the PDF version of the time off report."""
        if not request.session.get('timeoff_authenticated'):
            return request.redirect('/my/timeoff')
        
        email = request.session.get('timeoff_email')
        employee = request.env['hr.employee'].sudo().search([
            ('work_email', '=', email)
        ], limit=1)

        if not employee:
            return request.render('website.404')

        # Pre-calculate leave summary for the report
        leave_types = request.env['hr.leave.type'].sudo().search([])
        summary_data = leave_types.get_employees_days(
            [employee.id])[employee.id]
        leave_summary = []
        for lt in leave_types:
            stats = summary_data.get(lt.id, {})
            if stats.get('max_leaves', 0) > 0:
                leave_summary.append({
                    'name': lt.name,
                    'allocated': stats.get('max_leaves', 0),
                    'taken': stats.get('leaves_taken', 0),
                    'remaining': stats.get('remaining_leaves', 0),
                })

        # Generate the PDF report
        report_ref = 'employee_timeoff_report.action_report_employee_timeoff'
        data = {
            'leave_summary': leave_summary,
            'employee': employee,
            'timeoffs': request.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', 'not in', ('cancel', 'refuse'))
            ], order='date_from desc'),
            'datetime': datetime,
            'today': fields.Datetime.now(),
        }
        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            report_ref, res_ids=[employee.id], data=data)
        
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', 'attachment; '
                                     'filename="TimeOff_Report_%s.pdf"'
                                     % employee.name)
        ]
        
        # Clear session after report generation to force re-authentication on next access
        request.session['timeoff_authenticated'] = False
        request.session['timeoff_email'] = False

        return request.make_response(pdf_content, headers=pdfhttpheaders)

    @http.route('/my/timeoff/logout', type='http', auth="public", website=True)
    def timeoff_logout(self, **kwargs):
        """Clears the time off authentication session and redirects to the login page."""
        request.session['timeoff_authenticated'] = False
        request.session['timeoff_email'] = False
        return request.redirect('/my/timeoff')
