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
from odoo import fields, http
from odoo.http import request


class WebsiteForm(http.Controller):
    """Website form to request labour supply."""

    def _get_customers(self):
        """Customers the current user may create a request for."""
        if request.env.user._is_admin():
            return request.env['res.partner'].sudo().search([])
        return request.env.user.partner_id

    def _get_skills(self):
        """Skills of the current company offered on the form."""
        return request.env['skill.details'].sudo().search([
            ('company_id', '=', request.env.company.id)
        ])

    @http.route(['/labour_supply'], type='http', auth='user', website=True)
    def labour_supply(self):
        return request.render(
            'manpower_supply_management.labour_supply_single_form',
            {
                'skills': self._get_skills(),
                'customers': self._get_customers(),
                'error': False
            }
        )

    @http.route(['/labour_supply/submit_all'], type='http',
                auth='user', website=True, csrf=True)
    def labour_supply_submit_all(self, **post):
        """Validate the whole request first, then create the contract."""
        today = fields.Date.today()
        customer_id = post.get('customer_id')
        req_from = post.get('req_from_date')
        req_to = post.get('req_to_date')

        if not (customer_id and req_from and req_to):
            return self._reload_with_error(
                "Please fill in all required fields.")

        try:
            customer_id = int(customer_id)
            req_from = fields.Date.from_string(req_from)
            req_to = fields.Date.from_string(req_to)
        except (TypeError, ValueError):
            return self._reload_with_error("Invalid customer or date.")

        if customer_id not in self._get_customers().ids:
            return self._reload_with_error(
                "You are not allowed to request labour for this customer.")

        if req_from < today:
            return self._reload_with_error(
                "Contract start date cannot be before today.")

        if req_to < req_from:
            return self._reload_with_error(
                "Contract end date cannot be earlier than the start date.")

        form = request.httprequest.form
        allowed_skill_ids = self._get_skills().ids
        skill_lines = []
        errors = []

        for skill, s_from, s_to, qty in zip(
                form.getlist('skill_id'), form.getlist('line_from_date'),
                form.getlist('line_to_date'), form.getlist('line_qty')):

            if not (skill or s_from or s_to or qty):
                continue

            if not (skill and s_from and s_to and qty):
                errors.append(
                    "Each skill line must have Skill, From, To and Qty.")
                continue

            try:
                skill = int(skill)
                qty = int(qty)
                s_from = fields.Date.from_string(s_from)
                s_to = fields.Date.from_string(s_to)
            except (TypeError, ValueError):
                errors.append("Invalid value in a skill line.")
                continue

            if skill not in allowed_skill_ids:
                errors.append("Selected skill is not available.")
            elif s_from < today:
                errors.append("Skill date cannot start before today.")
            elif s_to < s_from:
                errors.append(
                    "Skill To Date cannot be earlier than From Date.")
            elif qty < 1:
                errors.append("Quantity must be at least 1.")
            else:
                skill_lines.append((0, 0, {
                    'skill_id': skill,
                    'from_date': s_from,
                    'to_date': s_to,
                    'number_of_labour_required': qty,
                }))

        if not errors and not skill_lines:
            errors.append("Please add at least one skill requirement.")

        if errors:
            return self._reload_with_error("\n".join(dict.fromkeys(errors)))

        # sudo is needed because website users only have read access on
        # labour.supply; the customer and every line were validated above.
        request.env['labour.supply'].sudo().create({
            'customer_id': customer_id,
            'from_date': req_from,
            'to_date': req_to,
            'skill_ids': skill_lines,
        })

        return request.render("manpower_supply_management.tmp_form_success")

    def _reload_with_error(self, msg):
        return request.render(
            'manpower_supply_management.labour_supply_single_form',
            {
                'skills': self._get_skills(),
                'customers': self._get_customers(),
                'error': msg
            }
        )
