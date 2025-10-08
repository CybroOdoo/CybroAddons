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
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal


class PatientPortal(portal.CustomerPortal):
    """Provide portal access for patients to view their treatment
    details, prescriptions, and invoices."""
    def _prepare_home_portal_values(self, counters):
        """Extends the base method to include the count of dental prescriptions
        in the returned dictionary if requested.
        Args:
            counters (list): A list of strings indicating which counts to
            include in the response."""
        values = super()._prepare_home_portal_values(counters)
        if 'prescriptions_count' in counters:
            prescriptions_count = request.env['dental.prescription'].sudo().search_count([])
            values['prescriptions_count'] = prescriptions_count
        return values

    @http.route(['/my/prescriptions'], type='http', auth="user", website=True)
    def portal_my_prescriptions(self, **kwargs):
        """Renders the prescriptions page for the logged-in user based on their role.
        Managers see all prescriptions, doctors see their own, and patients see
        their own prescriptions."""
        if request.env.ref('dental_clinical_management.group_dental_manager') in request.env.user.groups_id:
            domain = []
        elif request.env.ref('dental_clinical_management.group_dental_doctor') in request.env.user.groups_id:
            domain = [('prescribed_doctor_id', '=', request.env.user.partner_id.employee_ids.id)]
        else:
            domain = [('patient_id', '=', request.env.user.partner_id.id)]
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
