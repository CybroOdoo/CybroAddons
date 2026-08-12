# -*- coding: utf-8 -*-
#############################################################################

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
#############################################################################
"""Main controller for Theme Medicare. Handles all public website routes."""

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import pager as portal_pager


class ThemeMedicare(http.Controller):
    """Controller class handling website routes for the Medicare theme."""

    @http.route('/departments', type='http', auth="public", website=True, sitemap=True)
    def departments_page(self, **kw):
        """Render the departments page, optionally filtering by search query."""
        domain = [('active', '=', True)]
        search = kw.get('search')
        if search:
            domain.append(('name', 'ilike', search))

        departments = request.env['medicare.department'].sudo().search(domain)
        total_departments = request.env['medicare.department'].sudo().search_count([('active', '=', True)])

        return request.render('theme_medicare.departments_page', {
            'departments': departments,
            'search': search,
            'total_departments': total_departments,
        })

    @http.route(['/doctors', '/doctors/page/<int:page>'], type='http', auth="public", website=True, sitemap=True)
    def doctors_page(self, page=1, **kw):
        """Render the doctors directory page, filtering by department or search query."""
        domain = [('active', '=', True)]

        department_id = kw.get('department_id')
        search = kw.get('search')

        if department_id:
            domain.append(('department_id', '=', int(department_id)))
        if search:
            domain.append(('name', 'ilike', search))

        total_doctors = request.env['medicare.doctor'].sudo().search_count(domain)

        step = 8
        pager = portal_pager(
            url='/doctors',
            url_args={'department_id': department_id, 'search': search},
            total=total_doctors,
            page=page,
            step=step
        )

        doctors = request.env['medicare.doctor'].sudo().search(domain, limit=step, offset=pager['offset'])
        departments = request.env['medicare.department'].sudo().search([('active', '=', True)])

        return request.render('theme_medicare.doctors_page', {
            'doctors': doctors,
            'departments': departments,
            'department_id': department_id,
            'search': search,
            'total_doctors': total_doctors,
            'pager': pager,
        })

    @http.route('/patients', type='http', auth="public", website=True, sitemap=True)
    def patients_page(self, **kw):
        """Render the patient services information page."""
        return request.render('theme_medicare.patients_page')

    @http.route('/research', type='http', auth="public", website=True, sitemap=True)
    def research_page(self, **kw):
        """Render the medical research and clinical trials page."""
        return request.render('theme_medicare.research_page')

    @http.route('/about', type='http', auth="public", website=True, sitemap=True)
    def about_page(self, **kw):
        """Render the about us page."""
        return request.render('theme_medicare.aboutus_page')

    @http.route('/appointment', type='http', auth="public", website=True, sitemap=True)
    def appointment_page(self, **kw):
        """Render the appointment booking form with available doctors and departments."""
        departments = request.env['medicare.department'].sudo().search([('active', '=', True)])
        doctors = request.env['medicare.doctor'].sudo().search([('active', '=', True)])

        selected_department_id = False
        if kw.get('department_id'):
            try:
                selected_department_id = int(kw.get('department_id'))
            except ValueError:
                pass

        selected_doctor_id = False
        if kw.get('doctor_id'):
            try:
                selected_doctor_id = int(kw.get('doctor_id'))
            except ValueError:
                pass

        return request.render('theme_medicare.appointment_page', {
            'departments': departments,
            'doctors': doctors,
            'selected_department_id': selected_department_id,
            'selected_doctor_id': selected_doctor_id,
        })

    @http.route('/appointment/submit', type='http', auth="public", methods=['POST'], website=True, csrf=True)
    def appointment_submit(self, **kw):
        """Handle POST requests from the appointment booking form and create an appointment record."""
        # Support both custom page (first_name, last_name) and static snippet (patient_name)
        patient_name = kw.get('patient_name') or (kw.get('first_name', '') + ' ' + kw.get('last_name', '')).strip()

        # Support both ID (from dynamic pages) and String (from static snippet options)
        dept_val = kw.get('department_id') or kw.get('department_name')
        dept_id = False
        if dept_val:
            try:
                dept_id = int(dept_val)
            except ValueError:
                dept = request.env['medicare.department'].sudo().search([('name', '=ilike', dept_val)], limit=1)
                dept_id = dept.id if dept else False

        doc_val = kw.get('doctor_id') or kw.get('doctor_name')
        doc_id = False
        if doc_val:
            try:
                doc_id = int(doc_val)
            except ValueError:
                doc = request.env['medicare.doctor'].sudo().search([('name', '=ilike', doc_val)], limit=1)
                doc_id = doc.id if doc else False

        request.env['medicare.appointment'].sudo().create({
            'patient_name': patient_name,
            'phone': kw.get('phone'),
            'email': kw.get('email') or kw.get('email_from'),
            'date': kw.get('date'),
            'department_id': dept_id,
            'doctor_id': doc_id,
            'notes': kw.get('notes') or kw.get('description_note'),

            'date_of_birth': kw.get('dob'),
            'gender': kw.get('gender'),
            'appointment_type': kw.get('appointment_type'),
            'visit_mode': kw.get('visit_mode'),
            'preferred_time': kw.get('time'),
            'chief_complaint': kw.get('chief_complaint'),
            'insurance_provider': kw.get('insurance_provider'),
            'insurance_id': kw.get('insurance_id'),
            'current_medications': kw.get('current_medications'),
        })

        return request.render('theme_medicare.appointment_success_page')
