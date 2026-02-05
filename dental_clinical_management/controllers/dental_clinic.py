# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from io import BytesIO
from reportlab.pdfgen import canvas

from odoo.exceptions import UserError
from odoo import _, http
from odoo.http import Controller, request, route, content_disposition


class DentalClinic(Controller):
    """Controller for a dental clinic website that allows users to view clinic
    details and schedule appointments online."""

    @route('/dental_doctor', auth='public', website=True)
    def dental_clinic(self):
        """Renders the dental clinic page with patient, specialist, and doctor information.
        This method retrieves the current user's partner ID as the patient ID,
        fetches all records from the `dental.specialist` model, and all records
        from the `hr.employee` model to display on the dental clinic webpage."""
        patient_id = request.env.user.partner_id
        specialised_id = request.env['dental.specialist'].sudo().search([])
        doctor_id = request.env['hr.employee'].sudo().search([])
        return request.render('dental_clinical_management.website_dental_template',
                              {'patient_id': patient_id,
                               'specialised_id': specialised_id,
                               'doctor_id': doctor_id})

    @route('/create/appointment', auth='public', website=True)
    def create_appointment(self, **kw):
        """To create a new appointment from website"""
        if len(kw.get('time_shift')) == 0:
            raise UserError(self.env._('Doctor Doesnot have the available appointment'))
        else:
            patient_appointment = request.env['dental.appointment'].sudo().create({
                'patient_id': kw.get('patient'),
                'patient_phone': kw.get('phone'),
                'patient_age': kw.get('age'),
                'specialist_id': kw.get('specialization', False),
                'doctor_id': kw.get('doctor'),
                'shift_id': kw.get('time_shift'),
                'date': kw.get('date'),
            })
            return request.redirect(f'/success_appointment?token={patient_appointment.token_no}')

    @route('/success_appointment', auth='public', website=True)
    def success_appointment(self, **kwargs):
        """Return when appointment creation is success"""
        return request.render(
            'dental_clinical_management.website_rental_success_template', {'token': kwargs})

    @http.route('/dental_clinic/appointment_card/<int:token>',
                type='http', auth="public", website=True)
    def appointment_card(self, token):
        """To download the appointment card for patients for doctor's appointment"""
        appointment = request.env['dental.appointment'].sudo().browse(token)
        if not appointment.exists():
            return request.not_found()
        data = {
            'token': appointment.token_no,
            'doctor': appointment.doctor_id.name,
            'specialised': appointment.specialist_id.name,
            'appointment_time': appointment.shift_id.name,
            'date': appointment.date,
        }
        report_service = request.env['ir.actions.report']
        pdf_content, _ = report_service._render_qweb_pdf(
            'dental_clinical_management.action_appointment_card', data=data)
        pdf_http_headers = [('Content-Type', 'application/pdf'),
                            ('Content-Length', len(pdf_content))]
        return request.make_response(pdf_content, headers=pdf_http_headers)

    @route('/patient_details', type="json", auth='public', website=True)
    def get_patient_details(self, patient_id):
        """Retrieve and return details of a specific patient by their ID.
        This method accesses the `res.partner` model, retrieves a patient
        record by the given ID, and returns selected fields of the patient
        such as phone number and age.
        Args:
            patient_id (int): The unique identifier of the patient."""
        patient = request.env['res.partner'].sudo().browse(int(patient_id))
        return patient.read(fields=['phone', 'patient_age'])

    @route('/specialised_doctors', type="json", auth='public', website=True)
    def get_specialised_doctors(self, specialised_id):
        """To get the list of doctors based on their specialisation"""
        domain = []
        if specialised_id:
            domain = [('specialised_in_id', '=', int(specialised_id))]
        doctors = request.env['hr.employee'].sudo().search_read(domain, ["name"])
        return doctors

    @route('/doctors_shifts', type="json", auth='public', website=True)
    def get_doctors_shifts(self, doctor_id):
        """To get the particular doctor time slots"""
        doctors_shift = request.env['hr.employee'].sudo().browse(int(doctor_id)).time_shift_ids
        time_shifts = [{"id": rec.id, "name": rec.name} for rec in doctors_shift]
        return time_shifts

    @route('/all_doctors', auth='public', website=True)
    def get_all_doctors(self):
        """To list all the doctors"""
        doctor_id = request.env['hr.employee'].sudo().search([])
        return request.render('dental_clinical_management.website_all_doctors',
                              {'doctor_ids': doctor_id})
