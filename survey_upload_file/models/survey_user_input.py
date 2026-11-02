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
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class SurveyUserInput(models.Model):
    """
    This class extends the 'survey.user_input' model to add custom
    functionality for saving user answers.

    Methods:
        _save_lines: Save the user's answer for the given question
        _save_line_file:Save the user's file upload answer for the given
        question
        _get_line_answer_file_upload_values:
        Get the values to use when creating or updating a user input line
        for a file upload answer
    """
    _inherit = "survey.user_input"

    def _save_lines(self, question, answer, comment=None, overwrite_existing=True):
        """Save the user's answer for the given question."""
        if question.question_type != 'upload_file':
            return super()._save_lines(question, answer, comment, overwrite_existing)

        old_answers = self.env['survey.user_input.line'].search([
            ('user_input_id', '=', self.id),
            ('question_id', '=', question.id),
        ])
        if old_answers and not overwrite_existing:
            return super()._save_lines(question, answer, comment, overwrite_existing)

        return self._save_line_upload_file(question, old_answers, answer)

    def _save_line_upload_file(self, question, old_answers, answer):
        """
        Save uploaded files as survey answers by creating attachments and linking them
        to a survey.user_input.line record. If no valid files are provided, the answer is
        marked as skipped and existing records are updated or created accordingly.
        """
        vals = {
            'user_input_id': self.id,
            'question_id': question.id,
            'skipped': False,
            'answer_type': 'upload_file',
        }

        if not answer:
            vals.update({'skipped': True, 'answer_type': None, 'value_file_data_ids': [(6, 0, [])]})
            if old_answers:
                old_answers.value_file_data_ids.unlink()
                old_answers.write(vals)
                return old_answers
            return self.env['survey.user_input.line'].create(vals)

        file_data = answer[0] if isinstance(answer, (list, tuple)) and len(answer) > 0 else []
        file_names = answer[1] if isinstance(answer, (list, tuple)) and len(answer) > 1 else []
        has_existing_param = isinstance(answer, (list, tuple)) and len(answer) > 2
        raw_existing = answer[2] if has_existing_param else []

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

        old_attachments = old_answers.value_file_data_ids if old_answers else self.env['ir.attachment']

        if has_existing_param:
            if question.upload_multiple_file:
                kept_attachments = old_attachments.filtered(lambda a: a.id in existing_ids)
            else:
                if file_data and file_names:
                    kept_attachments = self.env['ir.attachment']
                else:
                    kept_attachments = old_attachments.filtered(lambda a: a.id in existing_ids)
        else:
            kept_attachments = self.env['ir.attachment']

        new_attachments = self.env['ir.attachment']
        for index, name in enumerate(file_names):
            if index >= len(file_data):
                break
            raw_content = file_data[index]
            if isinstance(raw_content, str):
                if raw_content.startswith('data:') and ',' in raw_content:
                    raw_content = raw_content.split(',', 1)[1]
                raw_content = raw_content.strip()
            new_attachments |= self.env['ir.attachment'].create({
                'name': name,
                'type': 'binary',
                'raw': raw_content,
                'public': True,
            })

        all_attachments = kept_attachments | new_attachments

        if not all_attachments:
            vals.update({'skipped': True, 'answer_type': None, 'value_file_data_ids': [(6, 0, [])]})
            if old_answers:
                old_answers.value_file_data_ids.unlink()
                old_answers.write(vals)
                return old_answers
            return self.env['survey.user_input.line'].create(vals)

        # Unlink only old attachments that were removed by the user
        attachments_to_remove = old_attachments - all_attachments
        if attachments_to_remove:
            attachments_to_remove.unlink()

        _logger.info(
            "[survey_upload_file] saved attachments for question %s: %s",
            question.id,
            [(attachment.name, attachment.file_size) for attachment in all_attachments],
        )

        vals['value_file_data_ids'] = [(6, 0, all_attachments.ids)]
        if old_answers:
            old_answers.write(vals)
            all_attachments.write({'res_model': 'survey.user_input.line', 'res_id': old_answers[:1].id})
            return old_answers

        line = self.env['survey.user_input.line'].create(vals)
        all_attachments.write({'res_model': 'survey.user_input.line', 'res_id': line.id})
        return line
