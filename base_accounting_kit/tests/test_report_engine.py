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
import ast
import csv
import io
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestReportEngine(AccountingKitTestCommon):
    """Shared engine of the dynamic reports: saved filters (SP.5), PDF page
    (P3.8: header, landscape, filter block), XLSX layout, file names."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.kit_entry(cls.ymd(2, 1), [(cls.kit_account('asset_receivable'), 500, 0, cls.partner_a),
                                      (cls.kit_account('income'), 0, 500, cls.partner_a)])
        cls.tb_action = cls.env.ref('base_accounting_kit.action_dynamic_trial_balance')
        cls.receivable_action = cls.env.ref('base_accounting_kit.action_dynamic_aged_receivable')
        cls.payable_action = cls.env.ref('base_accounting_kit.action_dynamic_aged_payable')

    def make_user(self, login, groups=('account.group_account_user',)):
        return self.env['res.users'].create({
            'name': login, 'login': login, 'company_id': self.company.id,
            'company_ids': [(6, 0, self.company.ids)],
            'group_ids': [(6, 0, [self.env.ref(g).id for g in groups])]})

    # ------------------------------------------------------------------ Saved filters
    def test_saved_filters(self):
        """Filters are saved on core ir.filters for the user and the menu:
        options without company / unfolded lines; one default per menu;
        private; other menus do not see them; forged options are checked
        again when applied."""
        user, other = self.make_user('kit_sf_a'), self.make_user('kit_sf_b')
        report = self.dyn('trial_balance').with_user(user)
        journal = self.kit_journal('sale')
        options = {'date_preset': 'last_quarter', 'target_move': 'all', 'journal_ids': journal.ids,
                   'display_account': 'all', 'unfolded': ['account_1'], 'comparison': {'periods': 2}}
        saved = report.action_save_filter(options, 'My TB', self.tb_action.id, False)
        record = self.env['ir.filters'].browse(saved[0]['id'])
        self.assertEqual(record.model_id, 'account.dynamic.report.trial_balance')
        self.assertEqual(record.action_id.id, self.tb_action.id)
        self.assertEqual(record.user_ids, user)
        stored = ast.literal_eval(record.context)
        self.assertEqual(stored['journal_ids'], journal.ids)
        self.assertFalse({'company_id', 'unfolded', 'date_from', 'date_to'} & set(stored))
        applied = report.get_report(saved[0]['options'])['options']
        self.assertEqual((applied['date_preset'], applied['comparison']['periods']), ('last_quarter', 2))
        report.action_save_filter(options, 'First', self.tb_action.id, True)
        filters = report.action_save_filter(options, 'Second', self.tb_action.id, True)
        self.assertEqual([f['name'] for f in filters if f['is_default']], ['Second'])
        self.assertEqual(self.dyn('trial_balance').with_user(other).get_saved_filters(self.tb_action.id), [])
        aged = self.dyn('aged').with_user(user)
        aged.action_save_filter({'account_type': 'receivable'}, 'Rec', self.receivable_action.id, False)
        self.assertEqual(aged.get_saved_filters(self.payable_action.id), [])
        with self.assertRaises(UserError):
            report.action_save_filter(options, '  ', self.tb_action.id, False)
        bad = self.env['ir.filters'].create({
            'name': 'bad', 'model_id': 'account.dynamic.report.trial_balance', 'action_id': self.tb_action.id,
            'user_ids': [user.id], 'context': "{'date_preset': 'x', 'journal_ids': [999999999]}"})
        bad_options = next(f for f in report.get_saved_filters(self.tb_action.id) if f['id'] == bad.id)['options']
        checked = report.get_report(bad_options)['options']
        self.assertEqual((checked['date_preset'], checked['journal_ids']), ('this_year', []))
        with self.assertRaises(AccessError):
            self.env['ir.filters'].with_user(other).browse(record.id).unlink()

    # ------------------------------------------------------------------ PDF
    def test_pdf_page(self):
        """Report PDF: own page header (logo, company), footer with the print
        date and page x / y, kit A4 format; a soft grey panel with the title
        (no accent) and the period in words with the currency; header row without box,
        no grid; landscape only for wide tables."""
        self.company.write({'logo': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='})
        html = self.pdf_html('trial_balance', {})
        self.assertIn('data:image/png;base64', html)
        self.assertIn(self.company.name, html)
        footer = html.split('o_kit_pdf_footer')[1]
        self.assertIn('class="topage"', footer)
        self.assertIn('Printed ', footer)
        panel = html.split('o_kit_pdf_heading_panel')[1].split('<table')[0]
        self.assertIn('background-color: #f8f9fa', panel)
        self.assertIn('border-radius: 6px', panel)
        self.assertIn('o_kit_pdf_title', panel)
        self.assertIn('o_kit_pdf_heading_line', panel)
        title = html.split('o_kit_pdf_title')[1][:300]
        self.assertIn('font-size: 26px', title)
        self.assertNotIn('#71639e', html)
        self.assertIn('color: #212529', html.split('o_kit_pdf_heading_line')[1][:100])
        period = self.dyn('trial_balance').get_report({})['heading']['period']
        self.assertIn('%s · Amounts in %s' % (period, self.company.currency_id.name), html)
        self.assertNotIn('>Period<', html)
        self.assertNotIn('o_kit_pdf_filters_line', html)
        drafts = self.pdf_html('trial_balance', {'target_move': 'all'})
        self.assertIn('Including draft entries', drafts.split('o_kit_pdf_filters_line')[1][:200])
        self.assertIn('border: none; border-bottom: 2px solid', html)
        self.assertNotIn('border-left', html.split('<tbody')[1])
        self.assertNotIn('data-report-landscape="True"', html)
        self.assertIn('data-report-landscape="True"', self.pdf_html('trial_balance', {'comparison': {'periods': 2}}))
        self.assertIn('data-report-landscape="True"', self.pdf_html('aged', {}))
        action = self.env.ref('base_accounting_kit.action_report_kit_statement')
        self.assertEqual(action.paperformat_id, self.env.ref('base_accounting_kit.paperformat_accounting_report'))

    def test_currency_symbol_option(self):
        """Amounts without the currency symbol by default (the currency once,
        under the title); the option "Currency symbol in amounts" brings it
        back; kept by saved filters; XLSX names the currency."""
        report = self.dyn('trial_balance')
        self.assertFalse(report.get_report({})['options']['currency_symbol'])
        self.assertTrue(report.get_report({'currency_symbol': 1})['options']['currency_symbol'])
        self.assertEqual(report.get_report({})['currency_name'], self.company.currency_id.name)
        self.kit_entry(self.ymd(1, 10), [(self.kit_account('asset_current'), 1234.5, 0),
                                         (self.kit_account('income'), 0, 1234.5)])
        symbol = self.company.currency_id.symbol
        html = self.pdf_html('trial_balance', {})
        self.assertIn('1,234.50', html)
        self.assertNotIn(symbol, html.split('<tbody')[1])
        self.assertIn('Amounts in %s' % self.company.currency_id.name, html)
        self.assertIn(symbol, self.pdf_html('trial_balance', {'currency_symbol': True}).split('<tbody')[1])
        # XLSX: the symbol in the number format of the amounts when the
        # option is on (cells stay numbers), never when it is off
        amount = lambda sheet: next(cell for row in sheet.iter_rows() for cell in row
                                    if isinstance(cell.value, float | int) and not isinstance(cell.value, bool))
        self.assertNotIn(symbol, amount(self.xlsx_sheet('trial_balance', {})).number_format)
        with_symbol = amount(self.xlsx_sheet('trial_balance', {'currency_symbol': True}))
        self.assertIn(symbol, with_symbol.number_format)
        self.assertIsInstance(with_symbol.value, float | int)
        position = self.company.currency_id.position
        self.assertTrue(with_symbol.number_format.split(';')[0].startswith('"%s' % symbol) if position == 'before'
                        else with_symbol.number_format.split(';')[0].endswith('%s"' % symbol))
        values = [cell.value for row in self.xlsx_sheet('trial_balance', {}).iter_rows() for cell in row]
        self.assertTrue(any(isinstance(v, str) and self.company.currency_id.name in v for v in values))
        saved = report.action_save_filter({'currency_symbol': True}, 'With symbol', self.tb_action.id, False)
        self.assertTrue(saved[0]['options']['currency_symbol'])

    def test_negative_amounts_red(self):
        """Negative amounts are red in the PDF and in the XLSX (number format
        with [Red], cells stay numbers); positive ones are not."""
        self.kit_entry(self.ymd(1, 10), [(self.kit_account('asset_current'), 500, 0),
                                         (self.kit_account('income'), 0, 500)])
        html = self.pdf_html('trial_balance', {})
        self.assertIn('color: #dc3545;', html.split('<tbody')[1])
        cells = [cell for row in self.xlsx_sheet('trial_balance', {}).iter_rows() for cell in row
                 if isinstance(cell.value, (int, float))]
        negative = next(cell for cell in cells if cell.value < 0)
        self.assertIn('[Red]', negative.number_format)

    def test_amount_units(self):
        """Amount unit option: as is (default), without decimals, in K, in M
        (1 decimal, suffix in each amount), with or without the symbol; the
        PDF prints them so; the XLSX keeps the exact amounts with a number
        format showing the unit; unknown values fall back to as is."""
        report = self.dyn('trial_balance')
        self.assertEqual(report.get_report({})['options']['amount_unit'], 'full')
        self.assertEqual(report.get_report({'amount_unit': 'x'})['options']['amount_unit'], 'full')
        self.kit_entry(self.ymd(1, 10), [(self.kit_account('asset_current'), 12345.6, 0),
                                         (self.kit_account('income'), 0, 12345.6)])
        body = lambda options: self.pdf_html('trial_balance', options).split('<tbody')[1]
        self.assertIn('12,345.60', body({}))
        self.assertIn('12,346', body({'amount_unit': 'int'}))
        self.assertNotIn('12,345.60', body({'amount_unit': 'int'}))
        self.assertIn('12.3K', body({'amount_unit': 'k'}))
        self.assertIn('0.0M', body({'amount_unit': 'm'}))
        symbol = self.company.currency_id.symbol
        self.assertIn(symbol, body({'amount_unit': 'k', 'currency_symbol': True}))
        cells = [cell for row in self.xlsx_sheet('trial_balance', {'amount_unit': 'k'}).iter_rows() for cell in row
                 if isinstance(cell.value, (int, float))]
        cell = next(c for c in cells if abs(c.value) == 12345.6)
        self.assertIn('"K"', cell.number_format)
        self.assertIn('[Red]', cell.number_format)

    def test_csv_and_xlsx_outline(self):
        """CSV (RI 3.15): header row, one row per line with its level as
        leading spaces, exact amounts with a dot whatever the amount unit;
        XLSX rows grouped by level (Excel outline)."""
        self.kit_entry(self.ymd(1, 10), [(self.kit_account('asset_current'), 12345.6, 0),
                                         (self.kit_account('income'), 0, 12345.6)])
        pl = self.env.ref('base_accounting_kit.account_financial_report_profitandloss0')
        options = {'account_report_id': pl.id, 'amount_unit': 'k', 'unfold_all': True}
        class Stream:
            data = b''
            def write(self, chunk):
                Stream.data += chunk
        class Response:
            stream = Stream()
        self.env['account.dynamic.report.financial'].get_csv_report(options, Response())
        text = Stream.data.decode('utf-8')
        self.assertTrue(text.startswith('\ufeff'))
        rows = list(csv.reader(io.StringIO(text[1:])))
        self.assertEqual(rows[0][1], 'Balance')
        screen = [line['columns'][0] for line in self.env['account.dynamic.report.financial'].get_report(
            options)['lines']]
        self.assertEqual([row[1] for row in rows[1:]],
                         ['%.2f' % (round(value, 2) or 0.0) if isinstance(value, float | int) else value
                          for value in screen])
        self.assertFalse(any(row[1] == '-0.00' for row in rows[1:]))
        self.assertTrue(any(row[1].endswith('.60') for row in rows[1:]))
        self.assertFalse(any('K' in cell for row in rows[1:] for cell in row[1:]))
        self.assertTrue(any(row[0].startswith('  ') for row in rows[1:]))
        sheet = self.xlsx_sheet('financial', {'account_report_id': pl.id, 'unfold_all': True})
        levels = {sheet.row_dimensions[i].outline_level for i in range(1, sheet.max_row + 1)}
        self.assertIn(1, levels)

    def test_csv_no_negative_zero(self):
        """QA Q3: float leftovers (-1e-11) and -0.0 are written 0.00 in the
        CSV, not -0.00; other amounts unchanged."""
        report = self.dyn('trial_balance')
        table = {'columns': [{'label': ''}, {'label': 'Balance', 'num': True}],
                 'rows': [{'cells': ['A', -1.0686562745831907e-11], 'indent': 0},
                          {'cells': ['B', -0.0], 'indent': 0},
                          {'cells': ['C', -12.34], 'indent': 0}]}
        data = {'options': {'company_id': self.company.id}}
        class Stream:
            data = b''
            def write(self, chunk):
                Stream.data += chunk
        class Response:
            stream = Stream()
        with patch.object(type(report), '_export_table', lambda self, options: (data, table)):
            report.get_csv_report({}, Response())
        rows = list(csv.reader(io.StringIO(Stream.data.decode('utf-8')[1:])))
        self.assertEqual([row[1] for row in rows[1:]], ['0.00', '0.00', '-12.34'])

    def test_statement_heading(self):
        """Heading of the screen (RI 1.5): no company, the period in words, the
        extra columns; shown by default, kept off when hidden."""
        report = self.dyn('trial_balance')
        data = report.get_report({'date_preset': 'custom', 'date_from': '%s-01-01' % self.year,
                                  'date_to': '%s-03-31' % self.year})
        self.assertTrue(data['options']['show_heading'])
        self.assertNotIn('company', data['heading'])
        self.assertEqual(data['heading']['period'], '1 January %s – 31 March %s' % (self.year, self.year))
        by_month = report.get_report({'date_preset': 'custom', 'date_from': '%s-01-01' % self.year,
                                      'date_to': '%s-03-31' % self.year, 'columns_by': 'month'})
        self.assertTrue(by_month['heading']['period'].endswith(', by month'))
        self.assertFalse(report.get_report({'show_heading': False})['options']['show_heading'])
        aged = self.dyn('aged').get_report({})
        self.assertTrue(aged['heading']['period'].startswith('As of '))
        bs = self.env.ref('base_accounting_kit.account_financial_report_balancesheet0')
        pl = self.env.ref('base_accounting_kit.account_financial_report_profitandloss0')
        year = {'date_preset': 'custom', 'date_from': '%s-01-01' % self.year, 'date_to': '%s-12-31' % self.year}
        financial = self.dyn('financial')
        self.assertEqual(financial.get_report(dict(year, account_report_id=bs.id))['heading']['period'],
                         'As of 31 December %s' % self.year)
        self.assertEqual(financial.get_report(dict(year, account_report_id=pl.id))['heading']['period'],
                         '1 January %s – 31 December %s' % (self.year, self.year))

    def test_pdf_branches(self):
        """With a branch selected the PDF lists it under "Branches"."""
        branch = self.env['res.company'].create({'name': 'Kit Branch', 'parent_id': self.company.id})
        self.env.user.company_ids |= branch
        report = self.env['account.dynamic.report.trial_balance'].with_context(
            allowed_company_ids=[self.company.id, branch.id])
        action = self.env.ref('base_accounting_kit.action_report_kit_statement')
        html = action.with_context(allowed_company_ids=[self.company.id, branch.id])._render_qweb_html(
            action.report_name, [], data=report.action_export_pdf({})['data'])[0].decode()
        self.assertIn('Branches: Kit Branch', html.split('o_kit_pdf_filters_line')[1][:200])

    def test_pdf_statement_lines(self):
        """PDF of the Profit and Loss as a statement: main sections on a grey
        band, a rule over the amounts of each "Total ..." line, rule over
        and double rule under the final total, zero amounts in light grey,
        negatives still red."""
        pl = self.env.ref('base_accounting_kit.account_financial_report_profitandloss0')
        options = {'account_report_id': pl.id}
        _data, table = self.dyn('financial')._export_table(options)
        kinds = {row['cells'][0]: row['kind'] for row in table['rows']}
        self.assertEqual(kinds['Income'], 'main')
        self.assertEqual(kinds['Total Income'], 'subtotal')
        self.assertIn('grand', kinds.values())
        rows = self.pdf_html('financial', options).split('<tbody')[1].split('</tr>')
        row = lambda name: next(r for r in rows if '>%s<' % name in r)
        self.assertIn('background-color: #f3f4f6', row('Income'))
        self.assertIn('border-top: 1px solid #495057', row('Total Income'))
        grand = next(name for name, kind in kinds.items() if kind == 'grand')
        self.assertIn('border-bottom: 3px double', row(grand))
        self.assertIn('color: #adb5bd', row('Other Income'))
        # a rounding rest is printed as a grey zero, not a red -0.00
        bs = self.env.ref('base_accounting_kit.account_financial_report_balancesheet0')
        self.assertNotIn('-0.00', self.pdf_html('financial', {'account_report_id': bs.id}))

    # ------------------------------------------------------------------ XLSX
    def test_xlsx_layout(self):
        """XLSX like the PDF: grid on screen only (not printed), tab named after the report; a
        light grey panel with the company, its address, the title (tall
        row), the period in words with the currency and the filters (no
        "label value" rows); the logo when the company has one; indent by
        cell format (no leading spaces), horizontal lines only, a line over
        subtotal amounts, line over and double line under the final total,
        zeros in light grey; frozen header, fit to page width, print footer;
        landscape for wide tables."""
        self.company.write({'logo': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='})
        options = {'account_report_id': self.env.ref(
            'base_accounting_kit.account_financial_report_profitandloss0').id}
        sheet = self.xlsx_sheet('financial', options)
        self.assertNotEqual(sheet.sheet_view.showGridLines, False)
        self.assertFalse(sheet.print_options.gridLines)
        self.assertEqual(sheet.title, 'Profit and Loss')
        # row 1: the logo; then company, address, title, period
        self.assertEqual(len(sheet._images), 1)
        self.assertEqual(sheet._images[0].anchor._from.row, 0)
        self.assertEqual(sheet['A2'].value, self.company.name)
        self.assertEqual(sheet['A4'].value, 'Profit and Loss')
        self.assertEqual(sheet.row_dimensions[4].height, 30)
        period = self.dyn('financial').get_report(options)['heading']['period']
        self.assertEqual(sheet['A5'].value, '%s · Amounts in %s' % (period, self.company.currency_id.name))
        self.assertEqual(sheet['A1'].fill.fgColor.rgb[-6:], 'F8F9FA')
        self.assertNotIn('Period', self.sheet_values(sheet))
        self.assertIn('Printed ', sheet.oddFooter.left.text)
        rows = {row[0].value: row for row in sheet.iter_rows() if row[0].value}
        self.assertEqual(rows['Total Income'][1].border.top.style, 'thin')
        net = next(row for row in sheet.iter_rows() if row[1].border.bottom.style == 'double')
        self.assertTrue(net[1].value)
        self.assertEqual(rows['Other Income'][1].font.color.rgb[-6:], 'ADB5BD')
        drafts = self.xlsx_sheet('financial', dict(options, target_move='all'))
        self.assertEqual(drafts['A6'].value, 'Including draft entries')
        self.company.logo = False
        self.assertEqual(self.xlsx_sheet('financial', options)['A1'].value, self.company.name)
        self.assertTrue(sheet.freeze_panes)
        self.assertTrue(sheet.sheet_properties.pageSetUpPr.fitToPage)
        gross = next(row[0] for row in sheet.iter_rows() if row[0].value == 'Gross Profit')
        self.assertEqual(gross.alignment.indent, 1)
        self.assertIsNone(gross.border.left.style)
        self.assertEqual(gross.border.bottom.style, 'thin')
        self.assertNotEqual(sheet.page_setup.orientation, 'landscape')
        self.assertEqual(self.xlsx_sheet('aged', {}).page_setup.orientation, 'landscape')

    # ------------------------------------------------------------------ Names
    def test_file_names(self):
        """PDF and XLSX are named after the report and its period."""
        options = {'date_preset': 'custom', 'date_from': str(self.ymd(1, 1)), 'date_to': str(self.ymd(3, 31))}
        name = 'Trial Balance %s - %s' % (self.ymd(1, 1), self.ymd(3, 31))
        report = self.dyn('trial_balance')
        self.assertEqual(report._export_filename(options), name)
        self.assertEqual(report.action_export_xlsx(options)['data']['report_name'], name)

    def test_pdf_without_layout_wizard(self):
        """Printing does not open the document layout configurator first
        (the PDF has its own page header)."""
        self.company.external_report_layout_id = False
        action = self.dyn('trial_balance').action_export_pdf({})
        self.assertEqual(action['type'], 'ir.actions.report')
