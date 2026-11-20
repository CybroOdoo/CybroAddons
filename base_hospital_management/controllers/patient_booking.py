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
#############################################################################
import base64
import logging
from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PatientBooking(http.Controller):
    """Class for patient booking"""

    @http.route('/patient_booking', type='http', auth="public", website=True)
    def patient_booking(self):
        """Function for patient booking from website."""
        if request.env.user._is_public():
            return request.redirect('/web/login')
        today = fields.Date.today()
        domain = [('date', '=', today), ('state', '=', 'confirm')]
        allocations = request.env['doctor.allocation'].sudo().search(domain)
        doctors = []
        departments = []
        current_partner = request.env.user.partner_id
        for rec in allocations:
            if current_partner not in rec.mapped('op_ids.patient_id'):
                doctors.append({'id': rec.id, 'name': rec.name})
                if rec.department_id:
                    dep_info = {'id': rec.department_id.id, 'name': rec.department_id.name}
                    if dep_info not in departments:
                        departments.append(dep_info)
        attachment = request.env['ir.attachment'].sudo().search([
            ('res_id', '=', current_partner.id),
            ('res_model', '=', 'res.partner'),
        ], limit=1)
        access_token = ''
        if attachment:
            if not attachment.access_token:
                attachment.generate_access_token()
            access_token = attachment.access_token or ''
        values = {
            'user': request.env.user.name,
            'date': today,
            'doctors': doctors,
            'departments': departments,
            'card': bool(attachment),
            'attachment_id': attachment.id if attachment else False,
            'access_token': access_token,
        }
        return request.render(
            "base_hospital_management.patient_booking_form", values)

    @http.route('/patient_booking/success', type='http',
                website=True, csrf=False)
    def patient_booking_submit(self, **kw):
        """Function for submitting the patient booking"""
        if request.env.user.partner_id.patient_seq in ['New', 'User',
                                                       'Employee']:
            request.env.user.partner_id.sudo().write(
                {'patient_seq': request.env['ir.sequence'].sudo().next_by_code(
                    'patient.sequence')}) or 'New'
        outpatient = request.env['hospital.outpatient'].sudo().create({
            'patient_id': request.env.user.partner_id.id,
            'doctor_id': int(kw.get("doctor-name")),
            'op_date': kw.get("date"),
            'reason': kw.get("reason")
        })
        outpatient.sudo().action_confirm()
        return request.redirect('/my/home')

    @http.route('/patient_booking/get_doctors', type='jsonrpc', auth="public",
                website=True)
    def update_doctors(self, **kw):
        """Method for fetching doctor allocation for the selected date"""
        domain = [('date', '=', kw.get('selected_date')), ('state', '=', 'confirm')]
        departments = []
        doctors = []
        department = kw.get('department')
        if department:
            try:
                dept_id = int(department)
                domain.append(('doctor_id.department_id.id', '=', dept_id))
            except (ValueError, TypeError) as err:
                _logger.warning("Invalid department parameter '%s': %s", department, err)
        allocation = request.env['doctor.allocation'].sudo().search(domain)
        current_partner = request.env.user.partner_id
        for rec in allocation:
            if current_partner not in rec.mapped('op_ids.patient_id'):
                doctors.append({'id': rec.id, 'name': rec.name})
                if rec.department_id:
                    dep_info = {'id': rec.department_id.id, 'name': rec.department_id.name}
                    if dep_info not in departments:
                        departments.append(dep_info)
        return {'doctors': doctors, 'departments': departments}

    @http.route('/patient_card', type='http', auth="user", website=True)
    def patient_card(self):
        """Render patient card registration form."""
        return request.render("base_hospital_management.patient_card_form")

    @http.route('/patient_card/success', type='http', auth="user",
                website=True, methods=['POST'])
    def patient_card_submit(self, **kw):
        """Submit patient card form and create patient record."""
        gender = kw.get('gender')
        if gender == 'others':
            gender = 'other'
        elif gender not in ['male', 'female', 'other']:
            gender = False
        partner_vals = {
            'name': kw.get('pname'),
            'date_of_birth': kw.get('dob') or False,
            'gender': gender,
            'email': kw.get('mail') or False,
            'phone': kw.get('phone') or False,
            'city': kw.get('place') or False,
        }
        file_obj = kw.get('file')
        if file_obj and hasattr(file_obj, 'read'):
            partner_vals['image_1920'] = base64.b64encode(file_obj.read())
        partner = request.env['res.partner'].sudo().create(partner_vals)
        if not partner.patient_seq or partner.patient_seq in ['New', 'User', 'Employee']:
            partner.sudo().write({
                'patient_seq': request.env['ir.sequence'].sudo().next_by_code('patient.sequence') or 'New'
            })
        partner.sudo().action_generate_patient_card()
        return request.redirect('/my/home')
