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
from odoo import models


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
                old_answers.write(vals)
                return old_answers
            return self.env['survey.user_input.line'].create(vals)

        file_data = answer[0] if isinstance(answer, (list, tuple)) and len(answer) > 0 else []
        file_names = answer[1] if isinstance(answer, (list, tuple)) and len(answer) > 1 else []

        if isinstance(file_data, str) and file_data:
            file_data = json.loads(file_data)
        if isinstance(file_names, str) and file_names:
            file_names = json.loads(file_names)

        if not file_data or not file_names:
            vals.update({'skipped': True, 'answer_type': None, 'value_file_data_ids': [(6, 0, [])]})
            if old_answers:
                old_answers.write(vals)
                return old_answers
            return self.env['survey.user_input.line'].create(vals)

        attachments = self.env['ir.attachment']
        for index, name in enumerate(file_names):
            attachments |= self.env['ir.attachment'].create({
                'name': name,
                'type': 'binary',
                'datas': file_data[index],
                'public': True,
            })

        vals['value_file_data_ids'] = [(6, 0, attachments.ids)]
        if old_answers:
            old_answers.write(vals)
            attachments.write({'res_model': 'survey.user_input.line', 'res_id': old_answers[:1].id})
            return old_answers

        line = self.env['survey.user_input.line'].create(vals)
        attachments.write({'res_model': 'survey.user_input.line', 'res_id': line.id})
        return line
