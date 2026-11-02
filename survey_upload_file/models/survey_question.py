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
        if answer and isinstance(answer, (list, tuple)):
            file_data = answer[0] if len(answer) > 0 else []
            file_names = answer[1] if len(answer) > 1 else []
            raw_existing = answer[2] if len(answer) > 2 else []

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

            existing_ids = []
            if isinstance(raw_existing, str) and raw_existing:
                try:
                    loaded = json.loads(raw_existing)
                    if isinstance(loaded, list):
                        existing_ids = [int(x) for x in loaded if str(x).isdigit()]
                    else:
                        existing_ids = [int(x.strip()) for x in raw_existing.split(',') if x.strip().isdigit()]
                except Exception:
                    existing_ids = [int(x.strip()) for x in raw_existing.split(',') if x.strip().isdigit()]
            elif isinstance(raw_existing, (list, tuple, set)):
                existing_ids = [int(x) for x in raw_existing if str(x).isdigit()]

            has_new_files = bool(file_data and file_names)
            has_existing_files = bool(existing_ids)
            is_empty = not (has_new_files or has_existing_files)
        elif answer:
            is_empty = False

        if is_empty and self.constr_mandatory and not self.survey_id.users_can_go_back:
            return {self.id: self.constr_error_msg or 'This question requires an answer.'}
        return {}
