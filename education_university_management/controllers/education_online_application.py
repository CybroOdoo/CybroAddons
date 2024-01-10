# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
###############################################################################
import base64
from odoo import http
from odoo.http import request


class OnlineAdmission(http.Controller):
    """Controller for taking online admission"""

    @http.route('/university', type='http', auth='public', website=True)
    def university_contact_us(self):
        """To redirect to contact page."""
        return request.render('education_university_management.university')

    @http.route('/applyonline', type='http', auth='public', website=True)
    def online_admission(self):
        """To pass certain default field values
                                    to the website registration form."""
        vals = {
            'department': request.env['university.department'].sudo().search(
                []),
            'course': request.env['university.course'].sudo().search([]),
            'semester': request.env['university.semester'].sudo().search([]),
            'year': request.env['university.academic.year'].sudo().search([]),
            'doc_type': request.env['university.document.type'].sudo().search([
                                ])
        }
        return request.render(
            'education_university_management.online_admission',
            vals)

    @http.route('/admission/submit', type='http', auth='public',
                website=True)
    def register_admission(self, **vals):
        """ This will create a new student application with the values."""
        if vals:
            guardian = request.env['res.partner'].sudo().create({
                'name': vals.get('father'),
                'is_parent': True
            })
            application = request.env[
                'university.application'].sudo().create({
                    'name': vals.get('first_name'),
                    'last_name': vals.get('last_name'),
                    'mother_name': vals.get('mother'),
                    'father_name': vals.get('father'),
                    'mobile': vals.get('phone'),
                    'email': vals.get('email'),
                    'date_of_birth': vals.get('date'),
                    'academic_year_id': vals.get('academic_year'),
                    'mother_tongue': vals.get('tongue'),
                    'course_id': vals.get('course'),
                    'department_id': vals.get('department'),
                    'semester_id': vals.get('semester'),
                    'street': vals.get('communication_address'),
                    'per_street': vals.get('communication_address'),
                    'guardian_id': guardian.id,
                    'image': base64.b64encode((vals.get('image')).read())
                })
            doc_attachment = request.env['ir.attachment'].sudo().create({
                'name': vals.get('doc').filename,
                'res_name': 'Document',
                'type': 'binary',
                'datas': base64.encodebytes((vals.get('doc')).read()),
            })
            request.env['university.document'].sudo().create({
                'document_type_id': vals.get('doc_type'),
                'attachment_ids': doc_attachment,
                'application_ref_id': application.id
            })

        return request.render(
            "education_university_management.submit_admission", {})
