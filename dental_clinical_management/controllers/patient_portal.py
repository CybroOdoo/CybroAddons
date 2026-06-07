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
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal


class PatientPortal(portal.CustomerPortal):
    """Provide portal access for patients to view their treatment
    details, prescriptions, and invoices."""
    def _get_prescription_domain(self):
        """Returns domain to filter dental.prescription for the current user.
        - Managers see all
        - Doctors see only their own prescribed prescriptions
        - Patients/portal users see only their own prescriptions
        - Anyone else sees nothing"""
        user = request.env.user
        if user.has_group('dental_clinical_management.group_dental_manager'):
            return []
        if user.has_group('dental_clinical_management.group_dental_doctor'):
            employee_id = user.employee_id.id if user.employee_id else False
            if employee_id:
                return [('prescribed_doctor_id', '=', employee_id)]
            return [('id', 'in', [])]
        # Portal / patient — only their own
        return [('patient_id', '=', user.partner_id.id)]

    def _prepare_home_portal_values(self, counters):
        """Extends the base method to include the count of dental prescriptions
        in the returned dictionary if requested."""
        values = super()._prepare_home_portal_values(counters)
        if 'prescriptions_count' in counters:
            domain = self._get_prescription_domain()
            prescriptions_count = request.env['dental.prescription'].sudo().search_count(domain)
            values['prescriptions_count'] = prescriptions_count
        return values

    @http.route(['/my/prescriptions'], type='http', auth="user", website=True)
    def portal_my_prescriptions(self, **kwargs):
        """Renders the prescriptions page for the logged-in user based on their role.
        Managers see all prescriptions, doctors see their own, and patients see
        their own prescriptions."""
        domain = self._get_prescription_domain()
        prescriptions = request.env['dental.prescription'].sudo().search(domain)
        return request.render("dental_clinical_management.portal_my_prescriptions",
                              {'prescriptions': prescriptions, 'page_name': 'prescriptions'})

    @http.route(['/view/prescriptions/<int:id>'],
                type='http', auth="public", website=True)
    def view_prescriptions(self, id):
        """View prescriptions based on the provided ID.
        :param id: The ID of the prescription to view.
        :return: Rendered template with prescription details."""
        prescription = request.env['dental.prescription'].browse(id)
        return request.render('dental_clinical_management.prescription_portal_template',
                              {'prescription_details': prescription, 'page_name': 'prescription'})
