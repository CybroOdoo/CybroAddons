# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM (odoo@cybrosys.com)
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
import logging
import re
from odoo import _, api, fields, models, release
from odoo.addons.iap.tools import iap_tools
from odoo.exceptions import UserError, ValidationError
from requests.exceptions import ConnectionError, Timeout

# Import of unknown third party lib
_logger = logging.getLogger(__name__)

DEFAULT_OLG_ENDPOINT = 'https://olg.api.odoo.com'


class HrAiScore(models.TransientModel):
    """
    Transient model / Wizard used to calculate the ATS score of an applicant's resume.
    Communicates with the Odoo AI service (OLG API) to analyze a candidate's CV
    against the configured job scoring criteria.
    """
    _name = "hr.ai.score"
    _description = "Wizard for calculating ats score"

    hr_shortlist_id = fields.Many2one(
        'hr.shortlist',
        string="Shortlisting Criteria",
        help="Select the configuration containing the criteria and weights to score this candidate against.",
        default=lambda self: self._get_default_shortlist()
    )
    hr_applicant_id = fields.Many2one(
        'hr.applicant',
        string="Applicant",
        help="The candidate whose resume is being evaluated and scored."
    )
    job_id = fields.Many2one(
        'hr.job',
        related='hr_applicant_id.job_id',
        string="Job Position",
        help="The target job position which provides requirements context for scoring."
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        domain="[('res_model', '=', 'hr.applicant'), ('res_id', '=', hr_applicant_id)]",
        string="Attachment",
        related='hr_applicant_id.message_main_attachment_id',
        readonly=False,
        help="The PDF or document attachment containing the candidate's CV/Resume text."
    )

    @api.model
    def _get_default_shortlist(self):
        """
        Retrieve the default shortlisting criteria configuration ID from system parameters.
        
        Returns:
            int: The ID of the default 'hr.shortlist' configuration if configured, otherwise False.
        """
        param = self.env['ir.config_parameter'].sudo().get_param(
            'hr_ai_recruitment.hr_shortlist')
        if param:
            return int(param)
        return False

    def action_calculate_score(self):
        """
        Initiate AI-based ATS score calculation for the selected applicant and CV.

        Performs:
            - Validates that both the shortlisting criteria and CV attachment are present.
            - Constructs job details and scoring criteria context.
            - Calls the Odoo OLG API endpoint to analyze the candidate's CV details against criteria.
            - Extracts the calculated score using regex from the response.
            - Saves the score and the AI-generated summary back to the hr.applicant record.

        Raises:
            ValidationError: If configuration/files are missing, prompt is too long, or API returns error status.
            UserError: On network connection errors or timeouts.
        """
        if not (self.hr_shortlist_id and self.attachment_id):
            raise ValidationError(
                _("Please select shortlisting criteria and attachment"))

        job_details = {
            'title': self.job_id.name,
            'department': self.job_id.department_id.name,
            'job_location': self.job_id.address_id.name,
            'employment_type': self.job_id.contract_type_id.name,
            'description': self.job_id.description
        }

        score_criteria = self.env['hr.shortlist.line'].search_read(
            [('hr_shortlist_id', '=', self.hr_shortlist_id.id)],
            ['name', 'score']
        )

        criteria_text = ""
        for criteria in score_criteria:
            criteria_text += f"{criteria['name']} ({criteria['score']}%): Compare the candidate's qualifications for this criteria.\n"

        conversation_history = [{
            'role': 'user',
            'content': f"""Analyze the following candidate's CV and score them based on how well they match the job requirements. Use the scoring criteria below to evaluate the candidate. Provide a score out of 100.It is necessary to return the final score to the total_score variable without exceptions.
        Scoring Criteria:
        {criteria_text}"""
        }]
        try:
            # Get the endpoint from config parameter, defaulting to the constant
            olg_api_endpoint = self.env['ir.config_parameter'].sudo().get_param(
                'web_editor.olg_api_endpoint', DEFAULT_OLG_ENDPOINT)

            response = iap_tools.iap_jsonrpc(
                f"{olg_api_endpoint}/api/olg/1/chat",
                params={
                    'prompt': f"{job_details} {self.hr_applicant_id.cv_details}",
                    'conversation_history': conversation_history,
                    'version': release.version,
                },
                timeout=30  # Increased visibility of the timeout parameter
            )

            # 1. Handle OLG API Status Errors (response['status'])
            if response['status'] == 'success':
                # total_score = response.get('content', {}).get('total_score')
                match = re.search(r'total_score\s*=\s*(\d+)',
                                  response['content'])
                if match:
                    # Score successfully extracted
                    total_score = int(match.group(1))
                    if total_score is not None:
                        # **NOTE: Ensure ats_score is fields.Integer for this to work**
                        self.hr_applicant_id.ats_score = total_score
                        self.hr_applicant_id.cv_score_summary = response.get(
                            'content', '')
                else:
                    # AI returned content, but score extraction failed (REGEX FAIL)
                    raise ValidationError(
                        _("Total score not found in the AI response. The response format may have changed. Please contact your administrator."))

            elif response['status'] == 'error_prompt_too_long':
                # Specific error for excessive CV/Job details length
                _logger.error("API Error: Prompt too long")
                raise ValidationError(
                    _("The combined length of the CV and Job Description is too long for the AI service. Please shorten the job description."))

            else:
                # Generic OLG API failure (e.g., authentication, unexpected server response)
                _logger.error("API call failed with status: %s",
                              response['status'])
                raise ValidationError(
                    _("The AI service returned an error: %s. Please check the server logs." % response.get(
                        'message', 'Unknown Error')))

        # 2. Handle Network/Timeout Errors (requests.exceptions)
        except ConnectionError:
            _logger.error("API Error: Connection failed")
            raise UserError(
                _("Connection to the Odoo AI service failed. Please check your network connection and API endpoint configuration."))
        except Timeout:
            _logger.error("API Error: Request timed out")
            raise UserError(
                _("The AI service took too long to respond (30-second timeout exceeded). The server may be busy or the request is too complex."))

        # 3. Handle Other Exceptions (e.g., programming errors, unhandled internal IAP exceptions)
        except Exception as exc:
            _logger.exception(
                "A critical, unhandled error occurred during AI score calculation.")
            raise ValidationError(
                _("A critical failure occurred while calculating the score: %s. Please consult the system logs for details." % str(
                    exc)))
        return {'type': 'ir.actions.act_window_close'}
