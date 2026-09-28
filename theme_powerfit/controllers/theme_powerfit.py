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

import json

from odoo import http
from odoo.http import request

# Category sort order for the membership page display
_PLAN_CATEGORY_ORDER = {'basic': 0, 'standard': 1, 'premium': 2}


class ThemePowerfit(http.Controller):
    """Controller for Theme PowerFit custom pages."""

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

    def _trainer_to_dict(self, trainer):
        """Serialize an hr.employee trainer record for JSON consumption."""
        return {
            'id': trainer.id,
            'name': trainer.name or '',
            'image_url': '/web/image/hr.employee/%d/image_1920' % trainer.id,
            'job': trainer.job_id.name if trainer.job_id else 'Personal Trainer',
            'description': trainer.trainer_short_description or '',
            'experience': trainer.trainer_experience or 0,
            'clients': trainer.trainer_clients or 0,
            'rating': trainer.trainer_rating or 0.0,
            'instagram': trainer.trainer_instagram or '',
            'twitter': trainer.trainer_twitter or '',
            'linkedin': trainer.trainer_linkedin or '',
        }

    def _plan_to_dict(self, plan):
        """Serialize a product.template gym plan record for JSON consumption."""
        label = {
            'basic': 'Basic', 'standard': 'Standard', 'premium': 'Premium',
        }.get(plan.gym_plan_category or '', plan.name)
        price = plan.list_price or 0.0
        features_text = plan.membership_details or plan.description_sale or ''
        features = []
        for line in features_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            is_unavail = (
                line.startswith('x:') or line.startswith('X:')
                or line.startswith('- ')
            )
            text = line[2:].strip() if is_unavail else line
            features.append({'text': text, 'available': not is_unavail})
        contact_url = '/contactus?plan=%s&product=%s&price=%.0f' % (
            label, (plan.name or '').replace(' ', '+'), price,
        )
        return {
            'label': label,
            'price': '%.0f' % price,
            'description': plan.gym_plan_description or '',
            'features': features,
            'is_featured': plan.gym_plan_category == 'standard',
            'contact_url': contact_url,
        }

    @http.route(['/theme_powerfit/trainers/data'], type='http',
                auth="public", website=True, csrf=False)
    def trainers_data(self, **kw):
        """Return active gym trainers as JSON for client-side rendering.

        The trainers page/snippet arch is fully static (no t-if/t-foreach)
        so the website editor can reliably select/remove/duplicate it and
        its sibling sections. This endpoint is fetched by
        PowerfitCore._fetchTrainers() to fill in real trainer data when it
        exists; if empty, the JS leaves the static demo cards in place.
        """
        trainers = self._get_gym_trainers()
        data = [self._trainer_to_dict(trainer) for trainer in trainers]
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(['/theme_powerfit/membership/data'], type='http',
                auth="public", website=True, csrf=False)
    def membership_data(self, **kw):
        """Return active gym plans as JSON for client-side rendering.

        Same rationale as trainers_data(): the membership page/snippet
        arch stays static; PowerfitCore._fetchMembershipPlans() fetches
        this endpoint and swaps in real pricing cards when plans exist.
        """
        plans = self._get_gym_plans()
        data = [self._plan_to_dict(plan) for plan in plans]
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')],
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
