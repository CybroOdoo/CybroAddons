# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ajith V (odoo@cybrosys.com)
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
################################################################################
import io
import xlsxwriter
from odoo import api, fields, models, _
from odoo.tools import date_utils
from odoo.tools.safe_eval import json
from odoo.exceptions import ValidationError


class SurveyXlsReport(models.TransientModel):
    """This is the wizard model, We can filter the xls report using this
    model"""
    _name = 'survey.xlsx.report'
    _description = 'Survey XLSX Report '

    partner_id = fields.Many2one('res.partner', string="Partner",
                                 help="Select for getting the report of the "
                                      "user")
    survey_ids = fields.Many2many('survey.survey', string="Survey Ids",
                                  help="This field stores survey ids",
                                  readonly=True)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Updates the domain of the 'partner_id' field based on the partners
        who have completed the associated surveys.

        This method iterates over the survey records linked to the current record
        and searches for survey user inputs that are in a 'done' state. It collects
        the partners associated with these completed surveys and sets the domain
        for the 'partner_id' field accordingly.

        If no partners have completed the surveys, a ValidationError is raised.

        Raises:
            ValidationError: If no partners have participated in the survey.

        Returns:
            dict: A dictionary containing the domain for the 'partner_id' field,
                  limited to the IDs of partners who have completed the surveys.
        """
        partner_ids = []
        for rec in self.survey_ids:
            user_list = self.env['survey.user_input'].search(
                [('survey_id', '=', rec._origin.id), ('state', '=', 'done')])
            for dec in user_list.partner_id:
                if dec.id not in partner_ids:
                    partner_ids.append(dec.id)
        if not partner_ids:
            raise ValidationError(_(
                "There are no partners participating in this survey"))

        return {'domain': {'partner_id': [('id', 'in', partner_ids)]}}

    def action_print_survey_xlsx_report(self):
        """
            Generates and returns an XLSX report containing survey responses.

            This method is triggered by a button and compiles survey data into an
            Excel file. It iterates through all linked surveys, filters completed
            responses (in the 'done' state), and gathers relevant information such
            as survey name, creation date, respondent's name, question title, and
            corresponding answers.

            The collected data is organized by survey name and structured into a
            dictionary format, which is then passed to the report generation process.

            If a specific partner is selected, the method filters the survey
            responses to include only those from that partner.

            Returns:
                dict: An action that triggers the generation of an XLSX report with
                      the compiled survey data.

            The returned action dictionary includes:
            - 'type': Specifies the type of action (report generation).
            - 'data': Contains model name, options (including the formatted survey data),
                      output format, and report name.
            - 'report_type': Specifies the report type ('xlsx').
            """
        data_dict = {}

        for doc in self.survey_ids:
            domain = [('survey_id', '=', doc.id), ('state', '=', 'done')]
            if self.partner_id:
                domain.append(('partner_id', '=', self.partner_id.id))
            for record in self.env['survey.user_input'].search(domain):
                for rec in self.env['survey.user_input.line'].search(
                        [('user_input_id', '=', record.id)]):
                    data = {
                        'survey_name': rec.survey_id.title,
                        'create_date': rec.create_date,
                        'user_name': rec.user_input_id.partner_id.name,
                        'question': rec.question_id.title,
                        'answer': rec.display_name,
                    }
                    # Check if the survey_name is already in the dictionary
                    survey_name = data['survey_name']
                    if survey_name not in data_dict:
                        data_dict[
                            survey_name] = []
                    data_dict[survey_name].append(data)
        grouped_data_list = [
            {'survey_name': survey_name, 'partner_id': self.partner_id.name,
             'data': survey_data} for survey_name, survey_data in
            data_dict.items()]
        dict_data = {
            'record': grouped_data_list
        }
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'survey.xlsx.report',
                'options': json.dumps(dict_data,
                                      default=date_utils.json_default),
                'output_format': 'xlsx',
                'report_name': 'Survey Question Answer Report',
            },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, dict_data, response):
        """
            Generates an XLSX report from the provided data and writes it to the response.

            This method is responsible for creating an Excel report using the `xlsxwriter`
            library. It processes the survey data contained in `dict_data` and formats it
            into a structured XLSX report. The report includes details such as survey name,
            respondent name, response date, questions, and answers.

            Parameters:
                dict_data (dict): A dictionary containing the survey data to be included
                                  in the report. The dictionary should have a key 'record'
                                  which holds a list of survey response data.
                response (werkzeug.wrappers.Response): The HTTP response object where the
                                                       generated XLSX file will be written.

            The report's layout adjusts based on whether a specific partner is associated
            with the survey responses. If a partner is selected, the report will include
            the partner's name; otherwise, it will show general response data.

            The method does the following:
            - Creates an in-memory XLSX file.
            - Adds survey data to the worksheet.
            - Applies formatting to the headers and cells.
            - Writes the final XLSX file to the response stream.

            Returns:
                None: The function directly writes the XLSX report to the response object.
            """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        format21 = workbook.add_format({'font_size': 10, 'bold': True})
        font_size_8 = workbook.add_format({'font_size': 8})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        heading_row_height = 30
        if dict_data.get('record'):
            if dict_data['record']:
                row = 0
                for records in dict_data.get('record'):
                    sheet.write(row, 0, records['survey_name'], head)
                    sheet.set_row(sheet.dim_rowmax, heading_row_height)
                    sheet.merge_range(sheet.dim_rowmax, 0, sheet.dim_rowmax, 4,
                                      records['survey_name'],
                                      head)
                    row += 1
                    if not records.get('partner_id'):
                        sheet.set_column('A:A', 5)
                        sheet.set_column('B:B', 15)
                        sheet.set_column('C:C', 15)
                        sheet.set_column('D:D', 76)
                        sheet.set_column('E:E', 56)
                        sheet.write(row, 0, 'Sl no', format21)
                        sheet.write(row, 1, 'Name', format21)
                        sheet.write(row, 2, 'Date', format21)
                        sheet.write(row, 3, 'Question', format21)
                        sheet.write(row, 4, 'Answer', format21)
                        row += 1
                        a = 1
                        for datas in records.get('data'):
                            sheet.write(row, 0, a, font_size_8)
                            a = a + 1
                            sheet.write(row, 1, datas.get('user_name'),
                                        font_size_8)
                            sheet.write(row, 2, datas.get('create_date'),
                                        font_size_8)
                            sheet.write(row, 3, datas.get('question'),
                                        font_size_8)
                            sheet.write(row, 4, datas.get('answer'),
                                        font_size_8)
                            row += 1
                    else:
                        sheet.set_column('A:A', 5)
                        sheet.set_column('B:B', 15)
                        sheet.set_column('C:C', 76)
                        sheet.set_column('D:D', 56)
                        sheet.write(row, 0, 'Sl no', format21)
                        sheet.write(row, 1, 'Date', format21)
                        sheet.write(row, 2, 'Question', format21)
                        sheet.write(row, 3, 'Answer', format21)
                        row += 1
                        a = 1
                        for datas in records.get('data'):
                            sheet.write(row, 0, a, font_size_8)
                            a = a + 1
                            sheet.write(row, 1, datas.get('create_date'),
                                        font_size_8)
                            sheet.write(row, 2, datas.get('question'),
                                        font_size_8)
                            sheet.write(row, 3, datas.get('answer'),
                                        font_size_8)
                            row += 1
                workbook.close()
                output.seek(0)
                response.stream.write(output.read())
                output.close()
