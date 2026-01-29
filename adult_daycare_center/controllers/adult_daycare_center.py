# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request


class RoomBooking(http.Controller):
    """ Controller for assessment_request website page """
    @http.route(['/assessment_request'], type='http', auth="public",
                website=True)
    def assessment_request(self, **kw):
        """Function for render assessment request form"""
        values = {
            'guests': request.env['res.partner'].sudo().search([]),
            'rooms': request.env['crm.lead'].sudo().search([])
        }
        return request.render("adult_daycare_center.assessment_request_form",
                              values)

    @http.route(['/assessment_request/submit'], type='http', auth="public",
                website=True, csrf=False)
    def assessment_request_submit(self, **kw):
        """Function for assessment request submission"""
        lead = request.env['crm.lead'].sudo().create({
            'type': 'lead',
            'name': kw.get('subject'),
            'contact_name': kw.get('applicant_name'),
            'birth_date': kw.get('birth_date'),
            'gender': kw.get('gender'),
            'street': kw.get('street'),
            'city': kw.get('city'),
            'marital_status': kw.get('marital_status'),
            'present_living': kw.get('living_arrangement'),
            'medicaid': kw.get('medicaid'),
            'medicare': kw.get('medicare'),
            'supplemental_income': kw.get('sup_sec_income'),
            'interest_program': kw.get('why_interest'),
            'previous_experience': kw.get('experience'),
            'where_when': kw.get('where_when'),
            'living_with_whom': kw.get('living_with_whom'),
            'relationship_responsible_relative': kw.get('relation_with_living'),
            'nearest_relative': kw.get('nearest_relative'),
            'nearest_relative_relation': kw.get('nearest_relative_relation'),
            'employed_at': kw.get('employed_where'),
            'business_phone': kw.get('business_phone'),
            'emergency_name': kw.get('emergency_contact_1'),
            'applicant_relationship': kw.get('applicant_relation_1'),
            'emergency_address': kw.get('emergency_address_1'),
            'emergency_phone': kw.get('emergency_phone_1'),
            'first_emergency_name': kw.get('emergency_contact_2'),
            'second_applicant_relationship': kw.get('applicant_relation_2'),
            'first_emergency_address': kw.get('emergency_address_2'),
            'first_emergency_phone': kw.get('emergency_phone_2'),
            'physician_name': kw.get('physician_name'),
            'physician_address': kw.get('physician_address'),
            'physician_phone': kw.get('physician_phone'),
            'physician_last_visit': kw.get('physician_last_visit'),
            'dentist_name': kw.get('dentist_name'),
            'dentist_address': kw.get('dentist_address'),
            'dentist_phone': kw.get('dentist_phone'),
            'dentist_last_visit': kw.get('dentist_last_visit'),
            'transportation': kw.get('transport_provider'),
            'arrival_time': kw.get('arrive_time'),
            'departure_time': kw.get('departure_time'),
            'special_diet': kw.get('diet'),
            'diet_detail': kw.get('diet_detail'),
            'allergies': kw.get('allergies'),
            'request_assurance': kw.get('request_assurance'),
            'paid_by': kw.get('paid_by'),
            'paid_by_name': kw.get('paid_by_name'),
            'paid_by_phone': kw.get('paid_by_phone'),
            'your_email': kw.get('email'),
            'email_from': kw.get('email'),
            'hospital_name': kw.get('hospital_choice'),
        })
        vals = {
            'lead': lead,
        }
        return request.render(
            "adult_daycare_center.assessment_request_submit_template", vals)
