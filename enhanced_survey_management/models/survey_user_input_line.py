# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V  (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import json
import textwrap
from datetime import datetime
from odoo import api, fields, models, _


class SurveyUserInputLine(models.Model):
    """Inherited user input line to add custom answer types """
    _inherit = 'survey.user_input.line'

    answer_type = fields.Selection(
        selection_add=[('url', 'URL'),
                       ('many2one', 'Many2one'),
                       ('many2many', 'Many2many'),
                       ('week', 'Week'),
                       ('time', 'Time'),
                       ('color', 'Color'),
                       ('email', 'Email'),
                       ('month', 'Month'),
                       ('name', 'Name'),
                       ('matrix', 'Matrix'),
                       ('address', 'Address'),
                       ('selection', 'Selection'),
                       ('time', 'Time'),
                       ('password', 'Password'),
                       ('email', 'Email'),
                       ('range', 'Range'),
                       ('file', 'File'),
                       ('qr', 'Qrcode'),
                       ('barcode', 'Barcode')], help="Custom answer types")
    value_url = fields.Char(string='User URL',
                            help='Answer question type : URL')
    value_email = fields.Char(string='User Email',
                              help="Answer question type : Email")
    value_week = fields.Char(string='User Week',
                             help="Answer question type : Week")
    value_color = fields.Char(string='User Color',
                              help="Answer question type : Color")
    value_many2one = fields.Char(string='Survey Many2one',
                                 help="Answer question type : Many2one")
    value_many2one_option = fields.Char(string='Many2one selected',
                                        help="Answer question type : Selected")
    value_many2many = fields.Char(string='Survey Many2many',
                                  help="Answer question type : Many2many")
    value_time = fields.Float(string='Time Value',
                              help="Answer question type : Time")
    value_matrix = fields.Text(string='Custom Matrix Values',
                               help="Answer question type : Custom Matrix")
    value_selection = fields.Char(string='User Selection',
                                  help="Answer question type : Selection")
    value_password = fields.Char(string='Password Value',
                                 help="Answer question type : Password")
    value_range = fields.Char(string='Range Value',
                              help="Answer question type:Range")
    value_file = fields.Many2one('ir.attachment',
                                 string='Survey file',
                                 help="Answer question type : Attachment")
    filename = fields.Char(string='File', help="Attachment file name")
    file_data = fields.Binary(string='File Data',
                              help="Attachment file data",
                              related="value_file.datas")
    value_month = fields.Char(string='Month Value',
                              help="Answer question type : Month")
    value_address = fields.Text(string='Address Value',
                                help="Answer question type : Address")
    value_name = fields.Text(string='Name Values',
                             help="Answer question type : Full name")
    value_qr = fields.Char(string='Qr Values',
                           help="Answer question type : QRcode")
    value_barcode = fields.Char(string='Barcode Values',
                                help="Answer question type : Barcode")

    def get_value_time(self):
        """Function to return answer for question type time """
        if self.value_time:
            return datetime.strptime(str(self.value_time).replace('.', ':'),
                                     "%H:%M").strftime("%H:%M")
        return None


    def get_value_address(self, field):
        """Function to return answer for question type address"""
        data = json.loads(self.value_address)
        if data:
            question_id = self.question_id.id
            return data[f'{question_id}-{field}']
        return ''

    def get_value_matrix(self, item):
        """Function to return answer for custom matrix"""
        data = json.loads(self.value_matrix)
        if data:
            question_id = self.question_id.id
            return data[f'{item}-{question_id}']
        return None

    def get_value_name(self, field):
        """Function to return answer for Full name"""
        data = json.loads(self.value_name)
        if data:
            question_id = self.question_id.id
            return data[f'{question_id}-{field}']
        return ''

    @api.depends('answer_type')
    def _compute_display_name(self):
        """Override compute function to add custom answer display"""
        for line in self:
            # Mapping of answer_type to corresponding value
            answer_type_mapping = {
                'char_box': line.value_char_box,
                'text_box': textwrap.shorten(line.value_text_box, width=50,
                                             placeholder=" [...]") if line.value_text_box else None,
                'numerical_box': line.value_numerical_box,
                'time': line.value_time,
                'month': line.value_month,
                'address': line.value_address,
                'name': line.value_name,
                'url': line.value_url,
                'many2one': line.value_many2one_option,
                'many2many': line.value_many2many,
                'week': line.value_week,
                'email': line.value_email,
                'range': line.value_range,
                'matrix': line.value_matrix,
                'password': line.value_password,
                'signature': line.value_signature,
                'color': line.value_color,
                'selection': line.value_selection,
                'barcode': line.value_barcode,
                'qr': line.value_qr,
                'file': line.filename,
                'date': fields.Date.to_string(
                    line.value_date) if line.value_date else None,
                'datetime': fields.Datetime.to_string(
                    line.value_datetime) if line.value_datetime else None,
            }

            # Special case for 'suggestion'
            if line.answer_type == 'suggestion':
                line.display_name = (
                    f"{line.suggested_answer_id.value}: {line.matrix_row_id.value}"
                    if line.matrix_row_id else line.suggested_answer_id.value
                )
            else:
                # Fetch value from mapping or default to 'Skipped'
                line.display_name = answer_type_mapping.get(line.answer_type,
                                                            None) or _('Skipped')
