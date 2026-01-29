# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
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
