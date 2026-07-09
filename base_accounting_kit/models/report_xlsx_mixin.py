# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from decimal import Decimal

import xlsxwriter

from odoo import models


def _json_default(value):
    """Serialise report cell values: keep numbers numeric (so xlsx applies a
    number format), stringify everything else (dates, recordsets, ...)."""
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


class ReportXlsxMixin(models.AbstractModel):
    """Generic xlsx export engine shared by the accounting report wizards.

    A wizard builds a normalised ``table`` dict and returns
    ``self._xlsx_action(report_name, table)``. ``action_manager.js`` turns the
    returned action into a POST to the ``/xlsx_report`` controller, which calls
    ``get_xlsx_report`` (below) to stream the workbook.

    ``table`` shape::

        {
          'title': str,
          'meta': [[label, value], ...],
          'columns': [{'label': str, 'width': int, 'num': bool}, ...],
          'rows': [{'cells': [...], 'bold': bool, 'indent': int}, ...],
        }
    """
    _name = 'account.report.xlsx.mixin'
    _description = 'Accounting Report XLSX Export Mixin'

    def _xlsx_action(self, report_name, table):
        """Return the client action that triggers the xlsx download."""
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': self._name,
                'options': json.dumps(table, default=_json_default),
                'output_format': 'xlsx',
                'report_name': report_name,
            },
            'report_type': 'xlsx',
        }

    def _xlsx_meta(self, form):
        """Standard heading rows (company, period, target moves)."""
        company = self.company_id or self.env.company
        if form.get('company_id'):
            company = self.env['res.company'].browse(form['company_id'][0])
        target = dict(
            self._fields['target_move'].selection).get(
            form.get('target_move'), '')
        period = '%s → %s' % (form.get('date_from') or '...',
                                   form.get('date_to') or '...')
        return [
            ['Company', company.name],
            ['Period', period],
            ['Target Moves', target or ''],
        ]

    def _ledger_table(self, title, meta, accounts_res):
        """Build a table for account-with-move-lines reports (bank/cash book,
        also reused by the general ledger)."""
        columns = [
            {'label': 'Date', 'width': 12},
            {'label': 'JRNL', 'width': 8},
            {'label': 'Partner', 'width': 28},
            {'label': 'Ref', 'width': 28},
            {'label': 'Move', 'width': 16},
            {'label': 'Debit', 'width': 16, 'num': True},
            {'label': 'Credit', 'width': 16, 'num': True},
            {'label': 'Balance', 'width': 16, 'num': True},
        ]
        rows = []
        for account in accounts_res:
            rows.append({'cells': [
                '%s %s' % (account['code'], account['name']), '', '', '', '',
                account['debit'], account['credit'], account['balance'],
            ], 'bold': True})
            for line in account['move_lines']:
                rows.append({'cells': [
                    line.get('ldate'), line.get('lcode'),
                    line.get('partner_name') or '', line.get('lname') or '',
                    line.get('move_name') or '', line.get('debit'),
                    line.get('credit'), line.get('balance'),
                ], 'indent': 1})
        return {'title': title, 'meta': meta, 'columns': columns,
                'rows': rows}

    def get_xlsx_report(self, data, response):
        """Stream a workbook built from the normalised ``data`` table."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        title_fmt = workbook.add_format({'bold': True, 'font_size': 18})
        meta_lbl = workbook.add_format({'bold': True})
        header = workbook.add_format(
            {'bold': True, 'bg_color': '#D9E1F2', 'border': 1,
             'align': 'center'})
        text = workbook.add_format({'border': 1})
        text_bold = workbook.add_format({'border': 1, 'bold': True})
        num = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        num_bold = workbook.add_format(
            {'border': 1, 'bold': True, 'num_format': '#,##0.00'})

        columns = data.get('columns', [])
        ncols = max(len(columns), 1)
        sheet.merge_range(0, 0, 0, ncols - 1,
                          data.get('title', 'Report'), title_fmt)
        row = 2
        for label, value in data.get('meta', []):
            sheet.write(row, 0, label, meta_lbl)
            sheet.write(row, 1, value)
            row += 1
        if data.get('meta'):
            row += 1

        for col_idx, col in enumerate(columns):
            sheet.set_column(col_idx, col_idx, col.get('width', 16))
            sheet.write(row, col_idx, col.get('label', ''), header)
        row += 1

        for line in data.get('rows', []):
            cells = line.get('cells', [])
            bold = line.get('bold')
            indent = line.get('indent', 0)
            for col_idx, col in enumerate(columns):
                val = cells[col_idx] if col_idx < len(cells) else ''
                if isinstance(val, dict):
                    # A translated (jsonb) field selected via raw SQL comes
                    # back as ``{lang: value}``; pick the active language.
                    lang = self.env.context.get('lang') or 'en_US'
                    val = val.get(lang) or next(iter(val.values()), '')
                if col.get('num') and isinstance(val, (int, float)) \
                        and not isinstance(val, bool):
                    sheet.write(row, col_idx, val,
                                num_bold if bold else num)
                else:
                    if col_idx == 0 and indent and val not in (None, ''):
                        val = ('    ' * indent) + str(val)
                    sheet.write(row, col_idx, val if val is not None else '',
                                text_bold if bold else text)
            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
