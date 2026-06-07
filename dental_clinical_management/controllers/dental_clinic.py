# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo.exceptions import UserError
from odoo import _
from odoo.http import Controller, request, route


class DentalClinic(Controller):
    """Controller for a dental clinic website that allows users to view clinic
    details and schedule appointments online."""

    @route('/dental_doctor', type='http', auth='public', website=True)
    def dental_clinic(self):
        """Renders the dental clinic page with patient, specialist, and doctor
        information.
        Retrieves the current user's partner record as the patient, fetches all
        dental.specialist records, and all hr.employee records to pass to the
        appointment form template.
        """
        patient_id = request.env.user.partner_id
        specialised_id = request.env['dental.specialist'].sudo().search([])
        doctor_id = request.env['hr.employee'].sudo().search([])
        return request.render(
            'dental_clinical_management.website_dental_template',
            {
                'patient_id': patient_id,
                'specialised_id': specialised_id,
                'doctor_id': doctor_id,
            }
        )

    @route('/create/appointment', type='http', auth='public', website=True)
    def create_appointment(self, **kw):
        """Create a new appointment submitted from the website form.
        Raises UserError if no time shift is selected, otherwise creates the
        dental.appointment record and redirects to the success page.
        """
        if not kw.get('time_shift'):
            raise UserError(_('Doctor does not have an available appointment slot.'))

        patient_appointment = request.env['dental.appointment'].sudo().create({
            'patient_id': kw.get('patient'),
            'patient_phone': kw.get('phone'),
            'patient_age': kw.get('age'),
            'specialist_id': kw.get('specialization', False),
            'doctor_id': kw.get('doctor'),
            'shift_id': kw.get('time_shift'),
            'date': kw.get('date'),
        })
        return request.redirect(
            f'/success_appointment?token={patient_appointment.token_no}&appointment_id={patient_appointment.id}'
        )

    @route('/success_appointment', type='http', auth='public', website=True)
    def success_appointment(self, **kwargs):
        """Render the success page after a new appointment is created."""
        return request.render(
            'dental_clinical_management.website_rental_success_template',
            {'token': kwargs}
        )

    @route('/dental_clinic/appointment_card/<int:appointment_id>',
           type='http', auth='public', website=True)
    def appointment_card(self, appointment_id):
        """Generate and return the appointment card PDF for a patient.
        The ``appointment_id`` URL segment is the record ID.
        """
        appointment = request.env['dental.appointment'].sudo().browse(appointment_id)
        if not appointment:
            return request.not_found()
        report_service = request.env['ir.actions.report']
        pdf_content, _ = report_service.sudo()._render_qweb_pdf(
            'dental_clinical_management.action_appointment_card',
            res_ids=[appointment.id],
        )
        pdf_http_headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition',
             f'inline; filename="appointment_{appointment.token_no}.pdf"'),
        ]
        return request.make_response(pdf_content, headers=pdf_http_headers)


    @route('/patient_details', type='jsonrpc', auth='public', website=True)
    def get_patient_details(self, patient_id):
        """Return phone and age for the given partner ID.
        Args:
            patient_id (int): res.partner record ID.
        Returns:
            list[dict]: One-element list with ``phone`` and ``patient_age``.
        """
        patient = request.env['res.partner'].sudo().browse(int(patient_id))
        if not patient.exists():
            return []
        return patient.read(fields=['phone', 'patient_age'])

    @route('/specialised_doctors', type='jsonrpc', auth='public', website=True)
    def get_specialised_doctors(self, specialised_id):
        """Return the list of doctors filtered by specialisation ID.
        Args:
            specialised_id (int | str): dental.specialist record ID, or empty
                string to return all doctors.
        Returns:
            list[dict]: Each dict contains ``id`` and ``name``.
        """
        domain = []
        if specialised_id and str(specialised_id).isdigit():
            domain = [('specialised_in_id', '=', int(specialised_id))]
        doctors = request.env['hr.employee'].sudo().search_read(
            domain, ['name']
        )
        return doctors

    @route('/doctors_shifts', type='jsonrpc', auth='public', website=True)
    def get_doctors_shifts(self, doctor_id):
        """Return available time shifts for the given doctor.
        Args:
            doctor_id (int | str): hr.employee record ID.
        Returns:
            list[dict]: Each dict contains ``id`` and ``name`` of the shift.
        """
        if not doctor_id or not str(doctor_id).isdigit():
            return []
        doctor = request.env['hr.employee'].sudo().browse(int(doctor_id))
        if not doctor.exists():
            return []
        return [{'id': rec.id, 'name': rec.name} for rec in doctor.time_shift_ids]

    @route('/all_doctors', type='http', auth='public', website=True)
    def get_all_doctors(self):
        """Render a page that lists all available doctors."""
        doctor_id = request.env['hr.employee'].sudo().search([])
        return request.render(
            'dental_clinical_management.website_all_doctors',
            {'doctor_ids': doctor_id}
        )
