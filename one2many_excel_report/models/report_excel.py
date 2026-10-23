# -*- coding: utf-8 -*-
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
#############################################################################
import io
import math
from odoo import models, fields

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class One2manyExcelReport(models.AbstractModel):
    """Abstract model helper to generate the Excel report."""
    _name = 'one2many.report.excel'
    _description = 'One2many Excel Report'

    def clean_data(self, value):
        if isinstance(value, str) and value.strip():
            parts = value.split()
            if len(parts) > 1 and parts[0].rstrip('.').isdigit():
                return ' '.join(parts[1:])
        return value

    def get_xlsx_report(self, data, names, response):
        """Used to print the excel report"""
        row_num = 7
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        date_style = workbook.add_format(
            {'text_wrap': True, 'bold': True, 'num_format': 'dd-mm-yyyy', 'valign': 'vcenter'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': 20, 'valign': 'vcenter'})
        txt = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})

        # Base column width setting
        total_cols = max(20, 6 + 3 * len(data))
        for col in range(total_cols):
            sheet.set_column(col, col, 15)

        sheet.merge_range('B2:I3', 'EXCEL REPORT', head)
        sheet.merge_range('A6:B6', 'Date:', date_style)
        sheet.merge_range('C6:D6', str(fields.Datetime.today()), date_style)

        # Field Labels
        for doc in names:
            row_num += 1
            col_num = 0
            sheet.merge_range(row_num, col_num + 2, row_num,
                              col_num + 4, str(doc), cell_format)

        # Record Data
        data_list = []
        for rec in data:
            for fname in names:
                val = rec.get(fname) if isinstance(rec, dict) else False
                if isinstance(val, (tuple, list)):
                    if len(val) > 1:
                        st = str(val[1])
                    elif len(val) == 1:
                        st = str(val[0])
                    else:
                        st = ''
                    data_list.append({'data': self.clean_data(st)})
                elif isinstance(val, dict):
                    lang = self.env.lang or 'en_US'
                    st = val.get(lang) or (next(iter(val.values())) if val else '')
                    data_list.append({'data': self.clean_data(str(st))})
                elif val is False or val is None:
                    data_list.append({'data': ''})
                elif isinstance(val, (int, float)):
                    data_list.append({'data': val})
                else:
                    data_list.append({'data': self.clean_data(str(val))})

        row_num = 7
        col_num = 4
        num = row_num + len(names)
        for doc in data_list:
            row_num += 1
            val_to_write = doc['data'] if doc['data'] is not None else ''
            sheet.merge_range(row_num, col_num + 2, row_num,
                              col_num + 4, val_to_write, txt)
            if row_num == num:
                col_num += 3
                row_num = 7

        # Dynamic column width and row height adjustment
        if names:
            num_fields = len(names)
            max_label_len = max([len(str(n)) for n in names], default=15)
            label_col_width = max(15, math.ceil((max_label_len + 4) / 3))
            sheet.set_column(2, 4, label_col_width)

            num_records = len(data)
            for rec_idx in range(num_records):
                rec_values = data_list[rec_idx * num_fields: (rec_idx + 1) * num_fields]
                max_rec_len = max(
                    [len(str(d['data'])) for d in rec_values if d.get('data') is not None],
                    default=15
                )
                target_3col_width = min(90, max(45, max_rec_len + 4))
                rec_col_width = math.ceil(target_3col_width / 3)
                col_start = 6 + 3 * rec_idx
                col_end = 8 + 3 * rec_idx
                sheet.set_column(col_start, col_end, rec_col_width)

            for f_idx in range(num_fields):
                r_idx = 8 + f_idx
                max_lines = 1
                for rec_idx in range(num_records):
                    val_idx = rec_idx * num_fields + f_idx
                    if val_idx < len(data_list):
                        val_str = str(data_list[val_idx]['data'] or '')
                        rec_values = data_list[rec_idx * num_fields: (rec_idx + 1) * num_fields]
                        max_rec_len = max(
                            [len(str(d['data'])) for d in rec_values if d.get('data') is not None],
                            default=15
                        )
                        target_3col_width = min(90, max(45, max_rec_len + 4))
                        lines = math.ceil(len(val_str) / max(1, target_3col_width))
                        if lines > max_lines:
                            max_lines = lines
                if max_lines > 1:
                    sheet.set_row(r_idx, max(25, max_lines * 18))
                else:
                    sheet.set_row(r_idx, 20)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


