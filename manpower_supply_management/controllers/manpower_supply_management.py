# -*- coding: utf-8 -*-
#############################################################################
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
###########################################################################
from odoo import http, fields
from odoo.http import request


class WebsiteForm(http.Controller):

    @http.route(['/labour_supply'], type='http', auth='user', website=True)
    def labour_supply(self):

        skills = request.env['skill.details'].sudo().search([
            ('company_id', '=', request.env.company.id)
        ])

        if request.env.user._is_admin():
            customers = request.env['res.partner'].sudo().search([])
        else:
            customers = request.env.user.partner_id

        return request.render(
            'manpower_supply_management.labour_supply_single_form',
            {
                'skills': skills,
                'customers': customers,
                'error': False
            }
        )

    @http.route(['/labour_supply/submit_all'], type='http',
                auth='user', website=True, csrf=True)
    def labour_supply_submit_all(self, **post):

        today = fields.Date.today()
        customer_id = post.get('customer_id')
        req_from = post.get('req_from_date')
        req_to = post.get('req_to_date')

        if not (customer_id and req_from and req_to):
            return self._reload_with_error("Please fill all required fields.")

        req_from = fields.Date.from_string(req_from)
        req_to = fields.Date.from_string(req_to)

        if req_from < today:
            return self._reload_with_error("Contract start date cannot be before today.")

        if req_to < req_from:
            return self._reload_with_error("Contract end date must be after start date.")

        order = request.env['labour.supply'].sudo().create({
            'customer_id': int(customer_id),
            'from_date': req_from,
            'to_date': req_to,
        })

        form = request.httprequest.form

        skills = form.getlist('skill_id')
        from_dates = form.getlist('line_from_date')
        to_dates = form.getlist('line_to_date')
        qty_list = form.getlist('line_qty')

        errors = []

        for i in range(len(skills)):

            skill = skills[i]
            s_from = from_dates[i]
            s_to = to_dates[i]
            qty = qty_list[i]

            if not (skill or s_from or s_to or qty):
                continue

            if not (skill and s_from and s_to and qty):
                errors.append(
                    "Each skill line must have Skill, From, To and Qty.")
                continue

            s_from = fields.Date.from_string(s_from)
            s_to = fields.Date.from_string(s_to)

            if s_from < today:
                errors.append("Skill date cannot start before today.")
                continue

            if s_to < s_from:
                errors.append("Skill To Date must be after From Date.")
                continue

            if int(qty) < 1:
                errors.append("Quantity must be at least 1.")
                continue

            order.sudo().write({
                'skill_ids': [(0, 0, {
                    'skill_id': int(skill),
                    'from_date': s_from,
                    'to_date': s_to,
                    'number_of_labour_required': int(qty),
                })]
            })

        if errors:
            return self._reload_with_error("\n".join(errors))

        return request.render("manpower_supply_management.tmp_form_success")

    def _reload_with_error(self, msg):

        skills = request.env['skill.details'].sudo().search([
            ('company_id', '=', request.env.company.id)
        ])

        if request.env.user._is_admin():
            customers = request.env['res.partner'].sudo().search([])
        else:
            customers = request.env.user.partner_id

        return request.render(
            'manpower_supply_management.labour_supply_single_form',
            {
                'skills': skills,
                'customers': customers,
                'error': msg
            }
        )

