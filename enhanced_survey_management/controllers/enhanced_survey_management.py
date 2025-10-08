# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Savad, Ahammed Harshad  (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http
from odoo.http import request


class SurveyAnswerPortal(CustomerPortal):
    """ Inherited CustomerPortal to add new portal view"""

    def _prepare_home_portal_values(self, counters):
        """ Function : Prepare portal values for attended survey count
            @return : Survey counts
        """
        values = super(SurveyAnswerPortal, self)._prepare_home_portal_values(
            counters)
        if 'survey_count' in counters:
            values['survey_count'] = request.env[
                'survey.survey'].sudo().search_count([
                ('user_id', '=', request.uid), ('visibility', '=', True)])
        return values


class SurveyPortalView(http.Controller):
    """ Survey portal controller """

    @http.route('/my/survey/ans', type='http', auth="public",
                website=True)
    def portal_my_survey(self):
        """ Controller to send survey data to portal """
        survey = request.env['survey.survey'].sudo().search(
            [('user_id', '=', request.uid)])
        values = {
            'survey_list': [{'id': rec.id,
                             'survey': rec.title,
                             'user_id': rec.user_id.name,
                             'email': rec.user_id.partner_id.email,
                             'status': rec.session_state
                             } for rec in survey if rec.visibility],
            'page_name': 'survey'
        }
        return request.render(
            """enhanced_survey_management.portal_survey_result""", values)

    @http.route('/my/survey/<int:survey_id>', type="http", auth="public",
                website=True)
    def survey_view(self, survey_id):
        """ Controller function to send specific survey data """
        question_list = []
        survey_questions_line = request.env[
            'survey.user_input.line'].sudo().search([
            ('survey_id', '=', survey_id)])
        survey = request.env['survey.survey'].sudo().browse(survey_id)
        for res in survey_questions_line:
            question_list.append({
                'id': res.question_id.id,
                'questions': res.question_id.title,
                'section': res.create_date,
                'question_type': res.question_id.question_type,
                'score': res.answer_score,
                'answer': res.display_name,
            })
        values = {
            'survey_questions': question_list,
            'survey': survey.title,
            'survey_date': survey.create_date,
            'name': survey.user_id.partner_id.name,
            'email': survey.user_id.partner_id.email,
            'access_token': survey.access_token,
            'page_name': 'survey',
            'survey_boolean': True
        }
        return request.render(
            "enhanced_survey_management.portal_survey_result_view", values)


class SurveyLoadContent(http.Controller):
    """Controller to load country and state to the survey"""

    @http.route('/survey/load_country', type="json", auth="public",
                website=True, csrf=False)
    def load_country(self):
        """Function to return country names for question type country"""
        country_ids = request.env['res.country'].sudo().search([])
        return {
            'id': country_ids.mapped('id'),
            'name': country_ids.mapped('name'),
        }

    @http.route('/survey/load_states', type="json", auth="public",
                website=True,
                csrf=False)
    def load_states(self, **kwargs):
        """Function to return state names based on country"""
        state_ids = request.env['res.country.state'].sudo().search([
            ('country_id.name', '=', kwargs['country_id'])
        ])
        return {
            'id': state_ids.mapped('id'),
            'name': state_ids.mapped('name'),
        }
