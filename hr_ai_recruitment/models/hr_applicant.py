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

import fitz
import logging
from odoo import api, fields, models

# Import of unknown third party lib
_logger = logging.getLogger(__name__)


class HRRecruitment(models.Model):
    """
        Extends the 'hr.applicant' model to include AI-powered recruitment
        features such as CV text extraction, automatic CV summarization,
        ATS scoring, and AI-based shortlisting.
        """
    _inherit = 'hr.applicant'

    cv_details = fields.Text(
        string="CV Contents",
        help="The extracted text content from the applicant's CV, "
             "automatically populated when a CV file is attached.",
        compute="_compute_cv_details",
    )
    cv_score_summary = fields.Text(
        string="CV Summary",
        help="A short AI-generated summary of the applicant's CV highlighting "
             "the key qualifications and experiences."
    )
    ats_score = fields.Integer(
        string="Resume Score",
        help="The score given to the CV based on ATS (Applicant Tracking System) "
             "analysis, indicating how well the CV matches the job requirements."
    )
    ai_shortlist_enabled = fields.Boolean(
        string="AI Shortlist Enabled",
        help="Indicates whether AI-based shortlisting is enabled.",
        compute='_compute_ai_shortlist_enabled'
    )

    @api.depends('message_main_attachment_id', 'attachment_ids')
    def _compute_cv_details(self):
        """
       Compute the `cv_details` field by extracting text content
       from the main CV attachment or any other attachments.

       Process:
           - If the applicant has a main attachment (`message_main_attachment_id`),
             extract text from it.
           - If there are other attachments, extract text from all of them.
           - If no attachments are found, set `cv_details` as an empty string.
       """
        for rec in self:
            if rec.message_main_attachment_id:
                rec.cv_details = self._extract_text_from_attachment(
                    rec.message_main_attachment_id)
            elif rec.attachment_ids:
                text = ""
                for attachment in rec.attachment_ids:
                    text += self._extract_text_from_attachment(attachment)
                rec.cv_details = text.strip()
            else:
                rec.cv_details = ""

    def _extract_text_from_attachment(self, attachment):
        """Helper method to extract text from a PDF attachment."""
        text = ""
        try:
            file_path = attachment._full_path(attachment.store_fname)
            doc = fitz.open(file_path)  # open a document
            for page in doc:  # iterate the document pages
                text += page.get_text(flags=8)
            text = '\n'.join(
                [line.strip() for line in text.splitlines() if
                 line.strip()])
        except Exception as e:
            _logger.error("Error extracting text from attachment %s: %s",
                          attachment.name, e)
        return text

    def action_ats_score(self):
        """
        Opens a wizard to calculate the ATS (Applicant Tracking System) score
        for the applicant's CV.

        Returns:
            dict: An Odoo action dictionary that opens the `hr.ai.score` form
            in a pop-up window, with the current applicant prefilled.
        """
        return {
            'name': 'Calculate Score',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.ai.score',
            'target': 'new',
            'context': {
                'default_hr_applicant_id': self.id,
            },
        }

    def _compute_ai_shortlist_enabled(self):
        """
        Compute whether AI shortlisting is enabled for the recruitment process.
        Logic:
            - Reads the `hr_ai_recruitment.is_ai_shortlist` system parameter.
            - Sets `ai_shortlist_enabled` to True if the parameter equals 'True'.

        This allows toggling AI shortlisting functionality globally.
        """
        ai_shortlist = self.env['ir.config_parameter'].sudo().get_param(
            'hr_ai_recruitment.is_ai_shortlist')
        for rec in self:
            rec.ai_shortlist_enabled = ai_shortlist == 'True'
