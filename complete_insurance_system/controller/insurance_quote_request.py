# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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
################################################################################
from odoo.http import Controller, request, route


class InsuranceQuoteRequest(Controller):

    @route('/insurance/request/form', methods=['GET'], auth='public',
           website=True)
    def insurance_request_form(self):
        """
        Render the insurance quote request form with values from different modules.

        :return: Rendered insurance quote request form with policy holders, providers, and policies.
        """
        return request.render(
            'complete_insurance_system.insurance_quote_request_form', {
                'policy_holder': request.env['res.partner'].sudo().search([]),
                'policy_provider': request.env['res.company'].sudo().search([]),
                'insurance_policy': request.env[
                    'insurance.policy'].sudo().search([]),
            })

    @route('/insurance/request/form/submit', type='http', auth='public',
           website=True, methods=['POST'])
    def insurance_request_form_submit(self, **post):
        """
        Handle the submission of the insurance quote request form.

        :param post: Dictionary containing form data.
        :return: Rendered thank you page after form submission.
        """
        request.env['res.insurance'].sudo().create({
            'policy_holder_id': post.get('holder'),
            'gender': post.get('gender'),
            'policy_provider_id': post.get('provider'),
            'insurance_policy_id': post.get('policy'),
            'dob': post.get('date_of_birth'),
            'age': post.get('age'),
            'phone': post.get('phone'),
            'email': post.get('email'),
        })
        return request.render("complete_insurance_system.thanks_form")
