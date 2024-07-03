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
from odoo import api, fields, models


class SurveyUserInputLine(models.Model):
    """
    This class extends the 'survey.user_input.line' model to add additional
    fields and constraints for file uploads.
    Methods:
        _check_answer_type_skipped:Check that a line's answer type is
        not set to 'upload_file' if the line is skipped
    """
    _inherit = "survey.user_input.line"

    answer_type = fields.Selection(
        selection_add=[('upload_file', 'Upload File')],
        help="The type of answer for this question (upload_file if the user "
             "is uploading a file).")
    value_file_data_ids = fields.Many2many('ir.attachment',
                                           help="The attachments "
                                                "corresponding to the user's "
                                                "file upload answer, if any.")

    @api.constrains('skipped', 'answer_type')
    def _check_answer_type_skipped(self):
        """ Check that a line's answer type is not set to 'upload_file' if
        the line is skipped."""
        for line in self:
            if line.answer_type != 'upload_file':
                super(SurveyUserInputLine, line)._check_answer_type_skipped()
