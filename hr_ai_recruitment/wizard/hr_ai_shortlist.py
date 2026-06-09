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

# imports of python lib
import logging

# imports of odoo
from odoo import _, api, fields, models
from odoo.addons.iap.tools import iap_tools
from odoo.exceptions import ValidationError

# Import of unknown third party lib
_logger = logging.getLogger(__name__)

DEFAULT_OLG_ENDPOINT = 'https://olg.api.odoo.com'


class AiShortlistWizard(models.TransientModel):
    """
    Transient model / Wizard to filter and shortlist job applicants.
    Allows selection of job applicants within a specific recruitment stage
    and filters them based on their ATS scores using comparison operators.
    """
    _name = "hr.ai.shortlist"
    _description = "Wizard for shortlisting"

    stage_id = fields.Many2one(
        'hr.recruitment.stage',
        string='Stage',
        help="The recruitment stage from which applicants will be loaded."
    )
    job_id = fields.Many2one(
        'hr.job',
        string="Job Position",
        help="The job position for which the shortlisting is executed."
    )
    applicant_ids = fields.Many2many(
        'hr.applicant',
        string="Applications",
        domain="([('stage_id', '=', stage_id), ('job_id', '=', job_id)])",
        help="The applicants to evaluate, automatically filtered by stage and job position."
    )
    required_score = fields.Integer(
        string="Required ATS Score",
        help="The threshold score used to compare applicant scores against."
    )
    operators = fields.Selection(
        [('=', '='), ('>', '>'), ('>=', '>='), ('<', '<'), ('<=', '<=')],
        string="Operator",
        help="The conditional operator used to filter applicant ATS scores against the required score."
    )

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """
        Dynamically update the listed applications when the recruitment stage changes.
        Loads all applicants in the specified stage and job position.
        """
        applicant_records = self.env['hr.applicant'].search(
            [('stage_id', '=', self.stage_id.id),
             ('job_id', '=', self.job_id.id)])
        self.applicant_ids = [fields.Command.link(id) for id in
                              applicant_records.ids]

    def action_application_shortlist(self):
        """
        Filter applicants based on ATS score and comparison operators,
        and assign them as shortlisted candidates to the job position.

        Validates operator selection, compares each applicant's ATS score, and
        updates the related job's shortlisted_applicant_ids. Returns a notification
        detailing the shortlist success.
        
        Returns:
            dict: An Odoo client action to show a desktop notification with the results.
        """
        if not self.operators:
            raise ValidationError(
                _("Please select an operator for conditional checking.")
            )

        filtered_applicants = self.env['hr.applicant']
        skipped_count = 0
        total_count = len(self.applicant_ids)

        for applicant in self.applicant_ids:
            if applicant.ats_score is not None:
                score = int(applicant.ats_score)
                if self.operators == '=' and score == self.required_score:
                    filtered_applicants |= applicant
                elif self.operators == '>' and score > self.required_score:
                    filtered_applicants |= applicant
                elif self.operators == '>=' and score >= self.required_score:
                    filtered_applicants |= applicant
                elif self.operators == '<' and score < self.required_score:
                    filtered_applicants |= applicant
                elif self.operators == '<=' and score <= self.required_score:
                    filtered_applicants |= applicant
            else:
                skipped_count += 1

        # Link shortlisted applicants to the job
        self.job_id.shortlisted_applicant_ids = [
            fields.Command.link(app.id) for app in filtered_applicants
        ]

        shortlisted_count = len(filtered_applicants)

        message = _(
            "%s applicants shortlisted successfully out of %s total.\n"
            "%s applicants skipped due to missing ATS score."
        ) % (shortlisted_count, total_count, skipped_count)

        message_type = "success" if shortlisted_count > 0 else "warning"

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Shortlisting Result'),
                'message': message,
                'type': message_type,
                'sticky': False,
            }
        }
