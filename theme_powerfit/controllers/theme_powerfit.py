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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Website controllers for Theme PowerFit."""

from odoo import http
from odoo.http import request

# Category sort order for the membership page display
_PLAN_CATEGORY_ORDER = {'basic': 0, 'standard': 1, 'premium': 2}


class ThemePowerfit(http.Controller):
    """Controller for PowerFit theme custom pages."""

    def _get_gym_trainers(self):
        """Return all active gym trainer employee records ordered by id."""
        return request.env['hr.employee'].sudo().search(
            [('is_gym_trainer', '=', True)],
            order='id asc',
        )

    def _get_gym_plans(self):
        """Return gym plan products ordered Basic → Standard → Premium.

        Fetches all product.template records with is_gym_plan=True and sorts
        them by category order (basic=0, standard=1, premium=2) so the website
        membership cards always display in the correct tier sequence.
        """
        plans = request.env['product.template'].sudo().search(
            [('is_gym_plan', '=', True), ('active', '=', True)],
        )
        return plans.sorted(
            key=lambda p: _PLAN_CATEGORY_ORDER.get(p.gym_plan_category or '', 99)
        )

    @http.route(['/services'], type='http', auth="public", website=True)
    def services_page(self, **kw):
        """Render the services page."""
        return request.render("theme_powerfit.powerfit_services_page")

    @http.route(['/trainers'], type='http', auth="public", website=True)
    def trainers_page(self, **kw):
        """Render the trainers page with dynamic gym trainer data.

        Passes all gym trainer records to the template. The template will
        display demo fallback cards when the list is empty.
        """
        trainers = self._get_gym_trainers()
        return request.render(
            "theme_powerfit.powerfit_trainers_page",
            {'trainers': trainers},
        )

    @http.route(['/membership'], type='http', auth="public", website=True)
    def membership_page(self, **kw):
        """Render the membership page with dynamic gym plan products.

        Passes gym plan products sorted Basic→Standard→Premium to the template.
        The template displays demo fallback cards when no gym plans are configured.
        """
        gym_plans = self._get_gym_plans()
        return request.render(
            "theme_powerfit.powerfit_membership_page",
            {'gym_plans': gym_plans},
        )

    @http.route(['/aboutus'], type='http', auth="public", website=True)
    def about_page(self, **kw):
        """Render the about us page."""
        return request.render("theme_powerfit.powerfit_about_us_page")

    @http.route(['/contactus'], type='http', auth="public", website=True)
    def contact_page(self, **kw):
        """Render the contact us page."""
        return request.render("theme_powerfit.powerfit_contact_us_page")
