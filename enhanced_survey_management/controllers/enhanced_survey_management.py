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
from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class SurveyAnswerPortal(CustomerPortal):
    """Inherited CustomerPortal to register survey counter values."""

    def _prepare_portal_counter_values(self, counter):
        """Return model, domain, and access mode for the survey portal counter."""
        if counter == 'survey_count':
            partner = request.env.user.partner_id
            domain = [
                ('partner_id', '=', partner.id),
                ('survey_id.visibility', '=', True),
                ('test_entry', '=', False),
            ]
            return 'survey.user_input', domain, 'sudo'
        return super()._prepare_portal_counter_values(counter)


class SurveyPortalView(http.Controller):
    """Survey portal controller."""

    @http.route('/my/survey/ans', type='http', auth="user", website=True)
    def portal_my_survey(self):
        """Display participant's attended surveys in the portal."""
        partner = request.env.user.partner_id
        user_inputs = request.env['survey.user_input'].sudo().search([
            ('partner_id', '=', partner.id),
            ('survey_id.visibility', '=', True),
            ('test_entry', '=', False),
        ])
        state_sel = dict(
            request.env['survey.user_input']._fields['state']
            ._description_selection(request.env),
        )
        values = {
            'survey_list': [{
                'id': rec.survey_id.id,
                'survey': rec.survey_id.title,
                'user_id': partner.name,
                'email': partner.email,
                'status': state_sel.get(rec.state, rec.state),
            } for rec in user_inputs],
            'page_name': 'survey',
        }
        return request.render(
            "enhanced_survey_management.portal_survey_result",
            values,
        )

    @http.route(
        '/my/survey/<int:survey_id>',
        type="http",
        auth="user",
        website=True,
    )
    def survey_view(self, survey_id):
        """Display participant answers for a specific survey in the portal."""
        partner = request.env.user.partner_id
        survey = request.env['survey.survey'].sudo().browse(survey_id)
        if not survey.exists() or not survey.visibility:
            return request.not_found()

        user_inputs = request.env['survey.user_input'].sudo().search([
            ('survey_id', '=', survey_id),
            ('partner_id', '=', partner.id),
        ])
        if not user_inputs:
            return request.redirect('/my/survey/ans')

        survey_questions_line = request.env[
            'survey.user_input.line'
        ].sudo().search([('user_input_id', 'in', user_inputs.ids)])

        question_list = [{
            'id': res.question_id.id,
            'questions': res.question_id.title,
            'section': res.create_date,
            'create_date': res.create_date,
            'question_type': res.question_id.question_type or res.answer_type,
            'score': res.answer_score,
            'answer': res.display_name,
        } for res in survey_questions_line]
        values = {
            'survey_questions': question_list,
            'survey': survey.title,
            'survey_date': survey.create_date,
            'name': partner.name,
            'email': partner.email,
            'access_token': survey.access_token,
            'page_name': 'survey',
            'survey_boolean': True,
        }
        return request.render(
            "enhanced_survey_management.portal_survey_result_view",
            values,
        )


class SurveyLoadContent(http.Controller):
    """Controller to load country and state options in surveys."""

    @http.route(
        '/survey/load_country',
        type="jsonrpc",
        auth="public",
        website=True,
    )
    def load_country(self):
        """Return country IDs and names for country selection questions."""
        country_ids = request.env['res.country'].sudo().search([])
        return {
            'id': country_ids.mapped('id'),
            'name': country_ids.mapped('name'),
        }

    @http.route(
        '/survey/load_states',
        type="jsonrpc",
        auth="public",
        website=True,
    )
    def load_states(self, country_id=None, **kwargs):
        """Return state IDs and names filtered by selected country."""
        country_name = (
            country_id
            or kwargs.get('country_id')
            or kwargs.get('params', {}).get('country_id')
        )
        country = (
            request.env['res.country'].sudo().search(
                [('name', '=', country_name)],
                limit=1,
            )
            if country_name else False
        )
        state_ids = (
            request.env['res.country.state'].sudo().search([
                ('country_id', '=', country.id),
            ])
            if country else request.env['res.country.state']
        )
        return {
            'id': state_ids.mapped('id'),
            'name': state_ids.mapped('name'),
        }
