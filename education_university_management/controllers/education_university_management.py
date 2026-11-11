# pylint: disable=unknown-option-value,missing-module-docstring
# pylint: disable=attribute-string-redundant
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal


class StudentPortal(CustomerPortal):
    """Controller for creating a new portal design for student users"""

    @http.route(['/home'], type='http', auth="user", website=True)
    def student_portal(self):
        """New portal for student users"""
        return request.render("education_university_management.student_portal")

    @http.route(['/student/info'], type='http', auth="user", website=True)
    def student_info(self):
        """Get basic details of students in the university"""
        values = request.env['university.student'].sudo().search([
            '|',
            ('partner_id', '=', request.env.user.partner_id.id),
            ('user_id', '=', request.env.user.id),
        ], limit=1)
        if not values:
            return request.redirect('/home')
        full_name = values.name or ''
        if values.middle_name:
            full_name = full_name + ' ' + values.middle_name
        if values.last_name:
            full_name = full_name + ' ' + values.last_name
        if values.gender == 'female':
            gender = 'Female'
        elif values.gender == 'male':
            gender = 'Male'
        else:
            gender = 'Other'
        vals = {
            'full_name': full_name,
            'student': values,
            'gender': gender,
        }
        return request.render("education_university_management.student_info",
                              {'values': vals})

    @http.route(
        ['/student/documents'], type='http', auth="user", website=True,
    )
    def student_documents(self):
        """Get documents of students in the university"""
        student = request.env['university.student'].sudo().search([
            '|',
            ('partner_id', '=', request.env.user.partner_id.id),
            ('user_id', '=', request.env.user.id),
        ], limit=1)
        app = (
            student.application_id if student
            else request.env['university.application']
        )
        docs = (
            request.env['university.document'].sudo().search(
                [('application_ref_id', '=', app.id)],
            ) if app else request.env['university.document']
        )
        attachment = request.env['ir.attachment'].sudo().browse(
            docs.attachment_ids.ids)
        attachment.public = True
        return request.render(
            "education_university_management.student_documents",
            {'docs': docs})

    @http.route(['/student/exam/results'], type='http', auth="user",
                website=True)
    def student_exam_result(self):
        """Get exam results of students in the university"""
        student = request.env['university.student'].sudo().search([
            '|',
            ('partner_id', '=', request.env.user.partner_id.id),
            ('user_id', '=', request.env.user.id),
        ], limit=1)
        exam = (
            request.env['exam.result'].sudo().search(
                [('student_id', '=', student.id)],
            ) if student else request.env['exam.result']
        )
        return request.render(
            "education_university_management.student_exam_result",
            {'data': exam})

    @http.route(['/student/result'], type='http', auth="user",
                website=True)
    def exam_subject(self):
        """Get subject wise exam results of students in the university"""
        student = request.env['university.student'].sudo().search([
            '|',
            ('partner_id', '=', request.env.user.partner_id.id),
            ('user_id', '=', request.env.user.id),
        ], limit=1)
        exam = (
            request.env['exam.result'].sudo().search(
                [('student_id', '=', student.id)], limit=1,
            ) if student else request.env['exam.result']
        )
        line = (
            request.env['results.subject.line'].sudo().search(
                [('result_id', '=', exam.id)],
            ) if exam else request.env['results.subject.line']
        )
        data = {
            'exam': exam,
            'line': line,
        }
        return request.render(
            "education_university_management.student_result", data)

    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        """ Override If the logged in user is a student,
                           they will be directed to the student portal."""
        values = self._prepare_portal_layout_values()
        is_student = request.env.user.partner_id.is_student or bool(
            request.env['university.student'].sudo().search_count([
                '|',
                ('partner_id', '=', request.env.user.partner_id.id),
                ('user_id', '=', request.env.user.id),
            ]),
        )
        if not is_student:
            return request.render("portal.portal_my_home", values)
        return request.redirect('/home')
