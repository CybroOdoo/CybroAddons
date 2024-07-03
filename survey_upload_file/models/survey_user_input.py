# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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

    def _save_lines(self, question, answer, comment=None,
                    overwrite_existing=False):
        """Save the user's answer for the given question."""
        old_answers = self.env['survey.user_input.line'].search([
            ('user_input_id', '=', self.id),
            ('question_id', '=', question.id), ])
        if question.question_type in 'upload_file':
            res = self._save_line_simple_answer(question, old_answers, answer)
        else:
            res = super()._save_lines(question, answer, comment,
                                      overwrite_existing)
        return res

    def _save_line_simple_answer(self, question, old_answers, answer):
        """ Save the user's file upload answer for the given question."""
        vals = self._get_line_answer_file_upload_values(question,
                                                        'upload_file', answer)
        if old_answers:
            old_answers.write(vals)
            return old_answers
        else:
            return self.env['survey.user_input.line'].create(vals)

    def _get_line_answer_file_upload_values(self, question, answer_type,
                                            answer):
        """Get the values to use when creating or updating a user input line
        for a file upload answer."""
        vals = {
            'user_input_id': self.id,
            'question_id': question.id,
            'skipped': False,
            'answer_type': answer_type,
        }
        if answer_type == 'upload_file':
            file_data = answer[0]
            file_name = answer[1]
            attachment_ids = []
            for file in range(len(answer[1])):
                attachment = self.env['ir.attachment'].create({
                    'name': file_name[file],
                    'type': 'binary',
                    'datas': file_data[file],
                })
                attachment_ids.append(attachment.id)
            vals['value_file_data_ids'] = attachment_ids
        return vals
