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
import json

from odoo import models


class SurveyUserInput(models.Model):
    """Inherited user input to save custom question answers."""

    _inherit = "survey.user_input"

    def _save_lines(self, question, answer, comment=None, overwrite_existing=True):
        """Save custom or standard survey question answers."""
        old_answers = self.env['survey.user_input.line'].search([
            ('user_input_id', '=', self.id),
            ('question_id', '=', question.id),
        ])
        custom_types = [
            'password', 'time', 'url', 'email', 'range', 'many2many',
            'file', 'many2one', 'week', 'color', 'month', 'address',
            'name', 'selection', 'qr', 'barcode',
        ]
        if question.question_type in custom_types or question.matrix_subtype == 'custom':
            return self._save_user_answers(question, old_answers, answer)
        return super()._save_lines(
            question, answer, comment, overwrite_existing=overwrite_existing,
        )

    def _save_user_answers(self, question, user_input_line, answer):
        """Create or update user input line with custom question answer values."""
        vals = self._get_user_answers(
            question, answer, question.question_type,
        )
        if user_input_line:
            user_input_line.write(vals)
        else:
            user_input_line = self.env['survey.user_input.line'].create(vals)
        return user_input_line

    def _get_user_answers(self, question, answer, answer_type):
        """Prepare answer value dictionary for custom question types."""
        vals = {
            'user_input_id': self.id,
            'question_id': question.id,
            'skipped': False,
            'answer_type': answer_type,
        }
        if not answer or (isinstance(answer, str) and not answer.strip()):
            vals.update(answer_type=None, skipped=True)
            return vals
        if question.question_type == 'time':
            vals['value_time'] = float(str(answer).replace(":", "."))
        elif question.question_type == 'url':
            vals['value_url'] = answer
        elif question.question_type == 'password':
            vals['value_password'] = answer
        elif question.question_type == 'email':
            vals['value_email'] = answer
        elif question.question_type == 'range':
            vals['value_range'] = answer
        elif question.question_type == 'many2one':
            vals['value_many2one'] = answer[0]
            vals['value_many2one_option'] = answer[1]
        elif question.question_type == 'many2many':
            vals['value_many2many'] = (
                ", ".join(str(item) for item in answer if item)
                if isinstance(answer, (list, tuple))
                else answer
            )
        elif question.question_type == 'week':
            vals['value_week'] = answer
        elif question.question_type == 'color':
            vals['value_color'] = answer
        elif question.question_type == 'month':
            vals['value_month'] = answer
        elif (
            question.question_type == 'matrix'
            and question.matrix_subtype == 'custom'
        ):
            vals['value_matrix'] = (
                json.dumps(answer) if not isinstance(answer, str) else answer
            )
        elif question.question_type == 'address':
            vals['value_address'] = (
                json.dumps(answer) if not isinstance(answer, str) else answer
            )
        elif question.question_type == 'qr':
            vals['value_qr'] = (
                answer if isinstance(answer, str) else json.dumps(answer)
            )
        elif question.question_type == 'barcode':
            vals['value_barcode'] = (
                answer if isinstance(answer, str) else json.dumps(answer)
            )
        elif question.question_type == 'name':
            vals['value_name'] = (
                json.dumps(answer) if not isinstance(answer, str) else answer
            )
        elif question.question_type == 'selection':
            vals['value_selection'] = answer
        elif question.question_type == 'file':
            attachment = self.env['ir.attachment'].create({
                'name': str(answer[1]), 'raw': answer[0], 'type': 'binary',
            })
            vals['value_file'] = int(attachment.id if attachment else False)
            vals['filename'] = attachment.name if attachment else False
        return vals

    def _save_line_matrix(self, question, old_answers, answers, comment=None):
        """Save custom matrix answers."""
        if question.matrix_subtype == 'custom':
            return self._save_user_answers(question, old_answers, answers)
        return super()._save_line_matrix(
            question, old_answers, answers, comment,
        )

    def _save_line_selection_answer(self, question, answer):
        """Save selection-type question answers."""
        vals = self._get_user_answers(
            question, answer, question.question_type,
        )
        return self.env['survey.user_input.line'].create(vals)
