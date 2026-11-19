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
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class WebsiteCustomerPortal(CustomerPortal):
    """Class for inheriting _prepare_home_portal_values function """

    def _prepare_portal_counter_values(self, counter):
        """Function for updating the badge counts of vaccinations, lab tests and op in Odoo 20 portal"""
        user = request.env.user
        partner = user.partner_id
        domain = ['|', ('patient_id', '=', partner.id), ('patient_id.user_ids', 'in', [user.id])]
        if counter == 'vaccination_count':
            return 'hospital.vaccination', domain, 'sudo'
        if counter == 'lab_test_count':
            return 'patient.lab.test', domain, 'sudo'
        if counter == 'op_count':
            return 'hospital.outpatient', domain, 'sudo'
        return super()._prepare_portal_counter_values(counter)

    def _prepare_home_portal_values(self, counters):
        """Function for updating the counts of vaccinations, lab tests and op
        of portal user"""
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        partner = user.partner_id
        domain = ['|', ('patient_id', '=', partner.id), ('patient_id.user_ids', 'in', [user.id])]
        if 'vaccination_count' in counters:
            values['vaccination_count'] = request.env[
                'hospital.vaccination'].sudo().search_count(domain)
        if 'lab_test_count' in counters:
            values['lab_test_count'] = request.env[
                'patient.lab.test'].sudo().search_count(domain)
        if 'op_count' in counters:
            values['op_count'] = request.env[
                'hospital.outpatient'].sudo().search_count(domain)
        return values
