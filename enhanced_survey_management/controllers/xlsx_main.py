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
import io
import json
from datetime import datetime

import xlsxwriter

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition


class XlsxReportController(http.Controller):
    """Controller to export survey answers as XLSX spreadsheets."""

    @http.route(
        '/xlsx_report/<model("survey.survey"):survey_id>',
        type='http',
        auth='user',
        csrf=False,
    )
    def get_report_xlsx(self, survey_id=None, **args):
        """Create and return an XLSX report for the selected survey."""
        survey_id.check_access('read')
        user_input_ids = request.env['survey.user_input'].search(
            [("survey_id", '=', survey_id.id)],
        )
        answers = []
        for rec in user_input_ids:
            answer = ''
            name = ''
            for new in rec.user_input_line_ids:
                if new.question_id.question_type in ['barcode', 'qr']:
                    continue
                new_dt = str(rec.create_date).split('.')
                if new.question_id.question_type == 'address':
                    if new.display_name and new.display_name != 'Skipped':
                        try:
                            data = json.loads(new.display_name)
                            for key in data:
                                if data[key]:
                                    answer += f'{data[key]},'
                        except (json.JSONDecodeError, TypeError):
                            answer = new.display_name
                    else:
                        answer = 'Skipped'
                    answers.append([
                        rec.id, rec.nickname, new_dt[0],
                        new.question_id.title, answer,
                    ])
                elif new.question_id.question_type == 'name':
                    if new.display_name and new.display_name != 'Skipped':
                        try:
                            data = json.loads(new.display_name)
                            for key in data:
                                if data[key]:
                                    name += f'{data[key]} '
                        except (json.JSONDecodeError, TypeError):
                            name = new.display_name
                    else:
                        name = 'Skipped'
                    answers.append([
                        rec.id, rec.nickname, new_dt[0],
                        new.question_id.title, name,
                    ])
                elif new.question_id.question_type == 'time':
                    time_str = new.display_name
                    if time_str == 'Skipped' or not time_str:
                        answers.append([
                            rec.id, rec.nickname, new_dt[0],
                            new.question_id.title, 'Skipped',
                        ])
                    else:
                        time_parts = time_str.split('.')
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
                        time_obj = datetime.strptime(
                            f'{hours}:{minutes}',
                            '%H:%M',
                        )
                        time_12hr = time_obj.strftime('%I:%M %p')
                        answers.append([
                            rec.id, rec.nickname, new_dt[0],
                            new.question_id.title, time_12hr,
                        ])
                else:
                    answers.append([
                        rec.id, rec.nickname, new_dt[0],
                        new.question_id.title, new.display_name,
                    ])
        answers.reverse()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column(1, 0, 25)
        sheet.set_column(2, 0, 25)
        sheet.set_column(3, 3, 50)
        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'center'},
        )
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'},
        )
        sub_title = workbook.add_format(
            {'align': 'right', 'bold': True, 'font_size': '12px'},
        )
        sub_title_content = workbook.add_format(
            {'align': 'left', 'bold': True, 'font_size': '12px'},
        )
        txt = workbook.add_format({'font_size': '10px'})
        sheet.merge_range('A2:D3', 'SURVEY MANAGEMENT REPORT', head)
        sheet.write('A4', 'Title :', sub_title)
        sheet.merge_range('B4:C4', survey_id.title, sub_title_content)
        sheet.merge_range('A6:A7', 'Partner', cell_format)
        sheet.merge_range('B6:B7', 'Submission Date & Time', cell_format)
        sheet.merge_range('C6:C7', 'Question', cell_format)
        sheet.merge_range('D6:D7', 'Answer', cell_format)
        column = 0
        for row, rec in enumerate(answers, start=7):
            sheet.write(row, column, rec[1], txt)
            sheet.write(row, column + 1, rec[2], txt)
            sheet.write(row, column + 2, rec[3], txt)
            sheet.write(row, column + 3, rec[4], txt)
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        output.close()
        return request.make_response(
            xlsx_data,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                (
                    'Content-Disposition',
                    content_disposition(survey_id.title + '.xlsx'),
                ),
            ],
        )
