# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
##############################################################################
import json
from odoo import fields, models


class SurveyQuestion(models.Model):
    """
    This class extends the 'survey.question' model to add new functionality
    for file uploads.
    """
    _inherit = 'survey.question'

    question_type = fields.Selection(
        selection_add=[('upload_file', 'Upload File')],
        help='Select the type of question to create.')
    upload_multiple_file = fields.Boolean(string='Upload Multiple File',
                                          help='Check this box if you want to '
                                               'allow users to upload '
                                               'multiple files')

    def validate_question(self, answer, comment=None):
        """
        Validate answers for questions of type 'upload_file' by checking whether the response
        contains valid file data and file names. If the question is mandatory and no valid
        files are provided while users cannot go back, a validation error is returned.
        """
        self.ensure_one()
        if self.question_type != 'upload_file':
            return super().validate_question(answer, comment)

        is_empty = True
        if answer and isinstance(answer, (list, tuple)) and len(answer) >= 2:
            file_data, file_names = answer[0], answer[1]
            if isinstance(file_data, str) and file_data:
                try:
                    file_data = json.loads(file_data)
                except Exception:
                    file_data = []
            if isinstance(file_names, str) and file_names:
                try:
                    file_names = json.loads(file_names)
                except Exception:
                    file_names = []
            is_empty = not (file_data and file_names)
        elif answer:
            is_empty = False

        if is_empty and self.constr_mandatory and not self.survey_id.users_can_go_back:
            return {self.id: self.constr_error_msg or 'This question requires an answer.'}
        return {}
