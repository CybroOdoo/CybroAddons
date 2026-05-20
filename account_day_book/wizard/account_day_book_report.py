# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or
#    sell copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
import io
import json
from datetime import date
from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.json import json_default

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DayBookWizard(models.TransientModel):
    """Wizard for generating PDF report and Excel report of day book."""
    _inherit = 'account.day.book.report'

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(_("Start Date cannot be greater than End Date."))

    def check_report(self):
        """Check if data exists before printing PDF."""
        form_data = self.read(['date_from', 'date_to', 'account_ids', 'journal_ids', 'target_move'])[0]
        active_acc = form_data.get('account_ids', [])
        accounts = self.env['account.account'].search(
            [('id', 'in', active_acc)]) if active_acc else self.env['account.account'].search([])
        accounts_res = self._get_account_move_entry(accounts, form_data)
        if not accounts_res:
            raise ValidationError(_('No report for the selected credentials'))
        return super(DayBookWizard, self).check_report()

    def report_xlsx(self):
        """Generate and return the data needed for the Excel report."""
        self.ensure_one()
        data = {'ids': self.env.context.get('active_ids', []),
                'model': self.env.context.get('active_model', 'ir.ui.menu'),
                'form': self.read(
                    ['date_from', 'date_to', 'account_ids', 'journal_ids',
                     'target_move'])[0]}
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                            lang=self.env.context.get(
                                                'lang') or 'en_US')
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'account.day.book.report',
                     'options': json.dumps(data,
                                           default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Day Book',
                     },
            'report_type': 'day_xlsx_download'
        }

    def _get_account_move_entry(self, accounts, form_data):
        """Retrieve account move entries based on specified criteria."""
        cr = self.env.cr
        if form_data['target_move'] == 'posted':
            target_move = "AND m.state = 'posted'"
        else:
            target_move = ''
        sql = (''' SELECT l.id AS lid, acc.name as accname,acc.code_store as acccode,
        l.account_id AS account_id, l.date AS ldate, j.code AS lcode,
        l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname,
        COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit,
        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,
        m.name AS move_name,m.id AS m_id, c.symbol AS currency_code, p.name AS partner_name
        FROM account_move_line l JOIN account_move m ON (l.move_id=m.id)
        LEFT JOIN res_currency c ON (l.currency_id=c.id)
        LEFT JOIN res_partner p ON (l.partner_id=p.id)
        JOIN account_journal j ON (l.journal_id=j.id)
        JOIN account_account acc ON (l.account_id = acc.id) 
        WHERE l.account_id IN %s AND l.journal_id IN %s ''' + target_move + '''
        AND l.date BETWEEN %s AND %s GROUP BY l.id, l.account_id, l.date,
        j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name,m.id,
        c.symbol, p.name , acc.name, acc.code_store
        ORDER BY l.date DESC
        ''')
        params = (tuple(accounts.ids), tuple(form_data['journal_ids']),
                  form_data['date_from'], form_data['date_to'])
        cr.execute(sql, params)
        return cr.dictfetchall()

    def get_xlsx_report(self, options, response):
        """Generate the Excel report based on the provided options and write it
         to the response."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data = {'form': options['form'], 'model': 'ir.ui.menu', 'ids': []}
        data['form']['used_context'] = {
            'date_to': options['form']['date_to'],
            'date_from': options['form']['date_from'],
            'strict_range': True,
            'state': options['form']['target_move'],
            'active_model': None,
            'active_ids': None,
            'active_id': None,
            'journal_ids': options['form']['journal_ids'],
            'account_ids': options['form']['account_ids'],
        }
        if not data.get('form'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))
        form_data = data['form']
        active_acc = data['form']['account_ids']
        accounts = self.env['account.account'].search(
            [('id', 'in', active_acc)]) if data['form']['account_ids'] else \
            self.env['account.account'].search([])
        accounts_res = self._get_account_move_entry(accounts, form_data)
        if not accounts_res:
            raise ValidationError('No report for the selected credentials')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format(
            {'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3',
             'bold': True})
        format2 = workbook.add_format(
            {'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format(
            {'font_size': 10, 'bold': True, 'align': 'left'})
        format4 = workbook.add_format({'font_size': 10})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format5 = workbook.add_format({'font_size': 10, 'align': 'right'})
        format8 = workbook.add_format(
            {'font_size': 10, 'bold': True, 'align': 'right'})
        format1.set_align('center')
        format2.set_align('center')
        format4.set_align('left')
        codes = [journal.code for journal in
                 self.env['account.journal'].search(
                     [('id', 'in', data['form']['journal_ids'])])]
        logged_users = self.env.company
        report_date = str(date.today())
        sheet.merge_range(0, 4, 0, 9, logged_users.name, format8)
        sheet.merge_range(0, 0, 0, 3, "Report Date : " + report_date, format6)
        sheet.merge_range(1, 0, 2, 9, "Day Book Report", format1)
        sheet.write('A4', "Journals :", format6)
        sheet.write('B4', "Journals :", format6)
        sheet.set_column('A:A', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('E:E', 23)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 38)
        sheet.set_default_row(28)
        journal_codes = ''
        for code in codes:
            journal_codes += code
            if journal_codes:
                journal_codes += ', '
        sheet.write('A4', "Journals :", format6)
        sheet.merge_range(3, 1, 3, 9, journal_codes, format4)
        if data['form']['target_move'] == 'all':
            target_moves = 'All entries'
        else:
            target_moves = 'All posted entries'
        if data['form']['date_from']:
            date_start = data['form']['date_from']
        else:
            date_start = ""
        if data['form']['date_to']:
            date_end = data['form']['date_to']
        else:
            date_end = ""
        sheet.write('H5', "Start Date", format3)
        sheet.write('H6', str(date_start), format4)
        sheet.write('J5', "End Date", format3)
        sheet.write('J6', str(date_end), format4)
        sheet.write('A5', "Target Moves", format6)
        sheet.write('A6', target_moves, format7)
        sheet.write('A8', "Date ", format2)
        sheet.write('B8', "JRNL", format2)
        sheet.write('C8', "Partner", format2)
        sheet.write('D8', "Ref", format2)
        sheet.write('E8', "Account", format2)
        sheet.write('F8', "Move", format2)
        sheet.write('G8', "Entry Label", format2)
        sheet.write('H8', "Debit", format2)
        sheet.write('I8', "Credit", format2)
        sheet.write('J8', "Balance", format2)
        row_number = 8
        col_number = 0
        company_id_str = str(self.env.company.id)
        lang = self.env.context.get('lang') or 'en_US'
        for lines in accounts_res:
            acc_code = lines['acccode'].get(company_id_str, '') if isinstance(lines['acccode'], dict) else lines['acccode'] or ''
            acc_name = lines['accname'].get(lang, '') if isinstance(lines['accname'], dict) else lines['accname'] or ''
            
            sheet.write(row_number, col_number, str(lines['ldate']), format4)
            sheet.write(row_number, col_number + 1, lines['lcode'], format4)
            sheet.write(row_number, col_number + 2, lines['partner_name'],
                        format4)
            sheet.write(row_number, col_number + 3, lines['lref'],
                        format4)
            sheet.write(row_number, col_number + 4,
                        acc_code + ' ' + acc_name,
                        format4)
            sheet.write(row_number, col_number + 5, lines['move_name'],
                        format4)
            sheet.write(row_number, col_number + 6, lines['lname'],
                        format4)
            sheet.write(row_number, col_number + 7, lines['debit'], format5)
            sheet.write(row_number, col_number + 8, lines['credit'], format5)
            sheet.write(row_number, col_number + 9,
                        lines['debit'] - lines['credit'], format5)
            row_number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
