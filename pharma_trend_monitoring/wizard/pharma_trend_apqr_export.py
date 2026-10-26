# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import io
import re
import statistics
from datetime import datetime, time

import xlsxwriter
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class PharmaTrendApqrExport(models.TransientModel):
    """XLSX of one product's trending data over a period, for the APQR.

    Produces the trending section QA otherwise assembles by hand: per watched
    parameter the results, mean and standard deviation, the range in force,
    the flagged count and a native Excel chart. A spreadsheet rather than a
    PDF, so QA can paste it into their own APQR template.
    """
    _name = 'pharma.trend.apqr.export'
    _description = 'APQR Trending Export'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Site',
        required=True,
        default=lambda self: self.env.company,
        help='Site whose results are exported.',
    )
    product_id = fields.Many2one(
        comodel_name='product.template',
        required=True,
        help='Product the review covers.',
    )
    date_from = fields.Date(
        string='From',
        required=True,
        default=lambda self: fields.Date.today() - relativedelta(years=1, days=-1),
        help='First day of the review period.',
    )
    date_to = fields.Date(
        string='To',
        required=True,
        default=fields.Date.today,
        help='Last day of the review period.',
    )
    parameter_ids = fields.Many2many(
        comodel_name='pharma.trend.parameter',
        string='Parameters',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]",
        help='Parameters to export. Leave empty for every watched parameter of the product.',
    )
    file_data = fields.Binary(string='File', readonly=True, attachment=False)
    file_name = fields.Char(readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Parameters chosen for another product no longer apply."""
        self.parameter_ids = self.parameter_ids.filtered(
            lambda p: p.product_id == self.product_id)

    def _parameters(self):
        """Parameters to export: the chosen ones, or every watched one of the product."""
        self.ensure_one()
        if self.parameter_ids:
            return self.parameter_ids
        return self.env['pharma.trend.parameter'].search([
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', self.company_id.id),
            ('is_trended', '=', True),
        ])

    def _period_results(self, param):
        """Approved results of a parameter tested within the period, oldest first."""
        self.ensure_one()
        start = datetime.combine(self.date_from, time.min)
        end = datetime.combine(self.date_to, time.max)
        return self.env['pharma.qc.result.line'].search([
            ('trend_parameter_id', '=', param.id),
            ('result_entered', '=', True),
            ('test_order_id.status', '=', 'passed'),
            ('test_order_id.create_date', '>=', start),
            ('test_order_id.create_date', '<=', end),
        ]).sorted(lambda line: (line.test_order_id.create_date, line.id))

    @staticmethod
    def _ranges_applied(lines):
        """Distinct normal ranges the results were evaluated against, in order of use."""
        ranges = []
        for line in lines.filtered('normal_range_applied'):
            key = (round(line.normal_range_low, 4), round(line.normal_range_high, 4))
            if key not in ranges:
                ranges.append(key)
        return ranges

    @staticmethod
    def _sheet_name(name, used):
        """A valid, unique worksheet name (31 characters, no []:*?/\\)."""
        base = re.sub(r'[\[\]:*?/\\]', ' ', name or 'Parameter').strip()[:31] or 'Parameter'
        candidate, n = base, 2
        while candidate.lower() in used:
            suffix = ' (%s)' % n
            candidate = base[:31 - len(suffix)] + suffix
            n += 1
        used.add(candidate.lower())
        return candidate

    def action_export(self):
        """Build the workbook and download it."""
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(self.env._('The start of the period must be before its end.'))
        params = self._parameters()
        if not params:
            raise UserError(self.env._('%s has no watched parameters to export.',
                                       self.product_id.display_name))
        content = self._build_workbook(params)
        period = '%s_%s' % (self.date_from, self.date_to)
        product = re.sub(r'[^\w.-]+', '_', self.product_id.name or 'product').strip('_')
        self.write({
            'file_data': base64.b64encode(content),
            'file_name': 'APQR_Trending_%s_%s.xlsx' % (product, period),
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=%s&id=%s&field=file_data&filename_field=file_name&download=true'
                   % (self._name, self.id),
            'target': 'self',
        }

    def _build_workbook(self, params):
        """The XLSX: a summary sheet and one sheet per parameter with its chart."""
        buffer = io.BytesIO()
        book = xlsxwriter.Workbook(buffer, {'in_memory': True})
        fmt = {
            'title': book.add_format({'bold': True, 'font_size': 14}),
            'bold': book.add_format({'bold': True}),
            'note': book.add_format({'italic': True, 'text_wrap': True, 'valign': 'top',
                                     'font_color': '#555555'}),
            'head': book.add_format({'bold': True, 'bg_color': '#DCE6F1', 'border': 1,
                                     'text_wrap': True, 'valign': 'vcenter'}),
            'cell': book.add_format({'border': 1}),
            'num': book.add_format({'border': 1, 'num_format': '0.0000'}),
            'date': book.add_format({'border': 1, 'num_format': 'yyyy-mm-dd'}),
            'flag': book.add_format({'border': 1, 'bg_color': '#FCE4D6'}),
            'flag_num': book.add_format({'border': 1, 'bg_color': '#FCE4D6', 'num_format': '0.0000'}),
        }
        stages = dict(params._fields['stage'].selection)
        period = '%s to %s' % (self.date_from, self.date_to)

        summary = book.add_worksheet(self.env._('Summary'))
        used = {summary.name.lower()}
        summary.write(0, 0, self.env._('Trending — %s', self.product_id.display_name), fmt['title'])
        summary.write(1, 0, self.env._('Site: %(site)s    Period: %(period)s',
                                       site=self.company_id.name, period=period))
        summary.merge_range(2, 0, 4, 11, self.env._(
            'This workbook is the trending section of the Annual Product Quality '
            'Review only: the results of each watched parameter, their mean and '
            'standard deviation, the normal range that applied, the results flagged '
            'outside it, and the trend chart. It is not a complete APQR — batches '
            'made, yields, deviations, CAPAs, change controls, complaints, returns '
            'and stability are not included.'
        ), fmt['note'])
        heads = [
            self.env._('Parameter'), self.env._('Stage'), self.env._('UoM'),
            self.env._('Spec. Min'), self.env._('Spec. Max'), self.env._('Results'),
            self.env._('Mean'), self.env._('Std. Deviation'), self.env._('Lowest'),
            self.env._('Highest'), self.env._('Normal Range Applied'),
            self.env._('Outside Normal Range'),
        ]
        summary.set_row(6, 30)
        for col, head in enumerate(heads):
            summary.write(6, col, head, fmt['head'])
        summary.set_column(0, 0, 28)
        summary.set_column(1, 9, 13)
        summary.set_column(10, 10, 34)
        summary.set_column(11, 11, 14)

        row = 7
        for param in params:
            lines = self._period_results(param)
            values = lines.mapped('actual_value')
            ranges = self._ranges_applied(lines)
            flagged = len(lines.filtered('outside_normal_range'))
            summary.write(row, 0, param.parameter_name, fmt['cell'])
            summary.write(row, 1, stages.get(param.stage, ''), fmt['cell'])
            summary.write(row, 2, param.uom or '', fmt['cell'])
            self._write_opt(summary, row, 3, param.spec_min if param.has_spec_min else None, fmt)
            self._write_opt(summary, row, 4, param.spec_max if param.has_spec_max else None, fmt)
            summary.write(row, 5, len(values), fmt['cell'])
            self._write_opt(summary, row, 6, statistics.fmean(values) if values else None, fmt)
            self._write_opt(summary, row, 7, statistics.stdev(values) if len(values) > 1 else None, fmt)
            self._write_opt(summary, row, 8, min(values) if values else None, fmt)
            self._write_opt(summary, row, 9, max(values) if values else None, fmt)
            summary.write(row, 10, '; '.join('%.4f – %.4f' % r for r in ranges)
                          or self.env._('None approved'), fmt['cell'])
            summary.write(row, 11, flagged, fmt['flag'] if flagged else fmt['cell'])
            self._write_parameter_sheet(
                book, self._sheet_name(param.parameter_name, used), param, lines, fmt, period)
            row += 1
        book.close()
        return buffer.getvalue()

    @staticmethod
    def _write_opt(sheet, row, col, value, fmt):
        """A number cell, or an empty bordered cell when there is no value."""
        if value is None:
            sheet.write_blank(row, col, None, fmt['cell'])
        else:
            sheet.write_number(row, col, value, fmt['num'])

    def _write_parameter_sheet(self, book, name, param, lines, fmt, period):
        """Results table, statistics and a line chart of one parameter."""
        sheet = book.add_worksheet(name)
        values = lines.mapped('actual_value')
        sheet.write(0, 0, param.name, fmt['title'])
        sheet.write(1, 0, self.env._('Period: %s', period))
        stats = [
            (self.env._('Results'), len(values)),
            (self.env._('Mean'), statistics.fmean(values) if values else None),
            (self.env._('Std. Deviation'), statistics.stdev(values) if len(values) > 1 else None),
            (self.env._('Outside Normal Range'), len(lines.filtered('outside_normal_range'))),
        ]
        for i, (label, value) in enumerate(stats):
            sheet.write(3 + i, 0, label, fmt['bold'])
            if value is not None:
                sheet.write_number(3 + i, 1, value, fmt['num'] if isinstance(value, float) else fmt['cell'])

        head_row = 8
        heads = [self.env._('Date'), self.env._('Batch'), self.env._('Test Order'), self.env._('Result'),
                 self.env._('Normal Range Low'), self.env._('Normal Range High'), self.env._('Spec. Min'),
                 self.env._('Spec. Max'), self.env._('Outside Normal Range'), self.env._('QA Note')]
        sheet.set_row(head_row, 30)
        for col, head in enumerate(heads):
            sheet.write(head_row, col, head, fmt['head'])
        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 2, 16)
        sheet.set_column(3, 8, 13)
        sheet.set_column(9, 9, 40)

        for i, line in enumerate(lines):
            r = head_row + 1 + i
            order = line.test_order_id
            out = line.outside_normal_range
            cell = fmt['flag'] if out else fmt['cell']
            sheet.write_datetime(r, 0, order.create_date, fmt['date'])
            sheet.write(r, 1, order.lot_id.name or '', cell)
            sheet.write(r, 2, order.name or '', cell)
            sheet.write_number(r, 3, line.actual_value, fmt['flag_num'] if out else fmt['num'])
            # Range columns left empty where no range applied: the chart line breaks there.
            self._write_opt(sheet, r, 4, line.normal_range_low if line.normal_range_applied else None, fmt)
            self._write_opt(sheet, r, 5, line.normal_range_high if line.normal_range_applied else None, fmt)
            self._write_opt(sheet, r, 6, param.spec_min if param.has_spec_min else None, fmt)
            self._write_opt(sheet, r, 7, param.spec_max if param.has_spec_max else None, fmt)
            sheet.write(r, 8, self.env._('Yes') if out else self.env._('No'), cell)
            sheet.write(r, 9, (order.normal_range_note or '') if out else '', cell)

        if lines:
            self._insert_chart(book, sheet, name, param, head_row, len(lines))
        else:
            sheet.write(head_row + 1, 0, self.env._('No approved results in this period.'), fmt['note'])

    def _insert_chart(self, book, sheet, name, param, head_row, count):
        """Native Excel line chart: results, the range in force and the specification."""
        first, last = head_row + 1, head_row + count
        chart = book.add_chart({'type': 'line'})
        categories = [name, first, 1, last, 1]

        def series(col, label, **style):
            """Add one line series for a worksheet column."""
            chart.add_series(dict({
                'name': label,
                'categories': categories,
                'values': [name, first, col, last, col],
            }, **style))

        series(3, self.env._('Result'), line={'color': '#1F4E79', 'width': 1.75},
               marker={'type': 'circle', 'size': 5,
                       'fill': {'color': '#1F4E79'}, 'border': {'color': '#1F4E79'}})
        series(4, self.env._('Normal Range Low'), line={'color': '#C55A11', 'dash_type': 'dash'})
        series(5, self.env._('Normal Range High'), line={'color': '#C55A11', 'dash_type': 'dash'})
        if param.has_spec_min:
            series(6, self.env._('Spec. Min'), line={'color': '#C00000', 'width': 1.25})
        if param.has_spec_max:
            series(7, self.env._('Spec. Max'), line={'color': '#C00000', 'width': 1.25})
        chart.set_title({'name': param.parameter_name, 'name_font': {'size': 12}})
        chart.set_x_axis({'name': self.env._('Batch'), 'num_font': {'rotation': -45}})
        chart.set_y_axis({'name': param.uom or self.env._('Result'),
                          'major_gridlines': {'visible': True, 'line': {'color': '#E0E0E0'}}})
        chart.set_legend({'position': 'bottom'})
        chart.show_blanks_as('gap')
        chart.set_size({'width': 760, 'height': 380})
        sheet.insert_chart(1, 11, chart)
