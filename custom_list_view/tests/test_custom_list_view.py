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
from odoo.tests import HttpCase, tagged
from odoo.tests.common import JsonRpcException, TransactionCase, new_test_user

def browser_code(body):
    """Wrap the test body in an async function reporting errors."""
    return (
        "(async () => {" + HELPERS + body + "})().catch("
        "(error) => console.error(`Test failed: ${error.message || error}`));"
    )


HELPERS = """
    const waitFor = async (selector) => {
        for (let i = 0; i < 150; i++) {
            const element = document.querySelector(selector);
            if (element) {
                return element;
            }
            await new Promise((resolve) => setTimeout(resolve, 100));
        }
        throw new Error(`Element not found: ${selector}`);
    };
    const buttonTexts = () => [
        ...document.querySelectorAll('.o_control_panel button'),
    ].map((button) => button.textContent.trim());
"""


@tagged('post_install', '-at_install')
class TestListViewReport(TransactionCase):
    """Test the PDF report template of the list view export."""

    def _render(self, header, rows):
        """Render the list view report with the given header and rows."""
        return self.env['ir.actions.report']._render_qweb_html(
            'custom_list_view.print_pdf_listview', [], data={
                'length': list(range(len(header))),
                'record': {'header': header, 'data': rows},
            })[0].decode()

    def test_01_report_action(self):
        """Verify the PDF report action is defined."""
        report = self.env.ref('custom_list_view.action_pdf_list_view')
        self.assertEqual(report.report_type, 'qweb-pdf')
        self.assertEqual(report.report_name,
                         'custom_list_view.print_pdf_listview')

    def test_02_report_renders_rows(self):
        """Verify the report renders one header cell per column and one
        cell per value.
        """
        html = self._render(['Name', 'Email'], [
            ['Alice', 'alice@example.com'],
            ['Bob', 'bob@example.com'],
        ])
        self.assertEqual(html.count('<th'), 2)
        self.assertEqual(html.count('<td'), 4)
        for value in ('Name', 'Email', 'Alice', 'bob@example.com'):
            self.assertIn(value, html)

    def test_03_report_without_columns(self):
        """Verify the report renders when no column is exported."""
        html = self._render([], [])
        self.assertNotIn('<td', html)


@tagged('post_install', '-at_install')
class TestListViewExportData(HttpCase):
    """Test the routes returning the list data to print or copy."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partners = cls.env['res.partner'].create([
            {'name': 'Test List Partner One', 'email': 'one@example.com'},
            {'name': 'Test List Partner Two', 'email': 'two@example.com'},
        ])
        cls.fields = [
            {'name': 'name', 'label': 'Name '},
            {'name': 'email', 'label': 'Email'},
        ]
        cls.no_export_user = new_test_user(
            cls.env, login='list_view_no_export', groups='base.group_user')

    def _params(self, **kwargs):
        """Return the route parameters for the test partners."""
        params = {
            'model': 'res.partner',
            'fields': self.fields,
            'res_ids': self.partners.ids,
            'domain': [],
        }
        params.update(kwargs)
        return params

    def test_01_get_data_with_ids(self):
        """Verify the data of the selected records is returned."""
        self.authenticate('admin', 'admin')
        result = self.make_jsonrpc_request('/get_data', self._params())
        self.assertEqual(result['header'], ['Name', 'Email'])
        self.assertEqual(result['data'], [
            ['Test List Partner One', 'one@example.com'],
            ['Test List Partner Two', 'two@example.com'],
        ])

    def test_02_get_data_with_domain(self):
        """Verify the records matching the domain are returned when no
        record is selected.
        """
        self.authenticate('admin', 'admin')
        result = self.make_jsonrpc_request('/get_data', self._params(
            res_ids=False,
            domain=[('name', '=like', 'Test List Partner%')]))
        self.assertEqual(len(result['data']), 2)

    def test_03_copy_data_has_header(self):
        """Verify the copied data starts with the column headers."""
        self.authenticate('admin', 'admin')
        result = self.make_jsonrpc_request('/get_data/copy', self._params())
        self.assertEqual(result[0], ['Name', 'Email'])
        self.assertEqual(len(result), 3)

    def test_04_export_permission_required(self):
        """Verify users without export permission can not get the data."""
        self.authenticate('list_view_no_export', 'list_view_no_export')
        for route in ('/get_data', '/get_data/copy'):
            with self.assertRaises(JsonRpcException):
                self.make_jsonrpc_request(route, self._params())


@tagged('post_install', '-at_install')
class TestListViewBrowser(HttpCase):
    """Test the list view features in the browser."""

    def test_01_row_numbers_pagination_and_buttons(self):
        """Verify the list shows the row numbers, the pagination text and
        the print and copy buttons.
        """
        self.env['res.partner'].create([
            {'name': f'Test Browser Partner {index}'} for index in range(3)])
        code = browser_code("""
            await waitFor('.o_list_view .o_data_row');
            const headers = [...document.querySelectorAll('.o_list_table thead th')]
                .map((th) => th.textContent.trim());
            if (!headers.includes('Sl No')) {
                throw new Error(`No Sl No column: ${headers}`);
            }
            const rows = document.querySelectorAll('.o_list_table .o_data_row');
            rows.forEach((row, index) => {
                const cell = row.querySelector('.o_list_record_selector + td');
                if (cell.textContent.trim() !== String(index + 1)) {
                    throw new Error(`Row ${index} numbered ${cell.textContent}`);
                }
            });
            const pagination = (await waitFor('.o_list_pagination')).textContent
                .replace(/\\s+/g, ' ');
            if (!/Showing from 1 - \\d+ of \\d+ Records/.test(pagination)) {
                throw new Error(`Bad pagination: ${pagination}`);
            }
            for (const text of ['PDF', 'Excel', 'CSV']) {
                if (!buttonTexts().includes(text)) {
                    throw new Error(`Missing ${text} button`);
                }
            }
            if (!document.querySelector('button[data-tooltip="Copy to Clipboard"]')) {
                throw new Error('Missing copy button');
            }
            console.log('test successful');
        """)
        self.browser_js(
            '/odoo/action-base.action_partner_form?view_type=list', code,
            login='admin')

    def test_02_copy_list_with_button_column(self):
        """Verify copying works on a list which contains a button column,
        and the copied text holds the headers and the records.
        """
        code = browser_code("""
            await waitFor('.o_list_view .o_data_row');
            let copied = null;
            Object.defineProperty(navigator, 'clipboard', {
                configurable: true,
                value: {writeText: async (text) => { copied = text; }},
            });
            document.querySelector('button[data-tooltip="Copy to Clipboard"]').click();
            const dialog = await waitFor('.modal-body');
            if (!dialog.textContent.includes('Records copied to clipboard.')) {
                throw new Error(`Unexpected dialog: ${dialog.textContent}`);
            }
            const lines = copied.split('\\n');
            if (lines.length < 2 || !copied.includes('English (US)')) {
                throw new Error(`Unexpected copy: ${copied}`);
            }
            console.log('test successful');
        """)
        self.browser_js(
            '/odoo/action-base.res_lang_act_window', code, login='admin')

    def test_03_buttons_hidden_without_export_permission(self):
        """Verify users without export permission do not see the buttons."""
        new_test_user(self.env, login='list_view_browser_user',
                      groups='base.group_user,base.group_partner_manager')
        code = browser_code("""
            await waitFor('.o_list_view .o_data_row');
            const found = buttonTexts().filter((text) =>
                ['PDF', 'Excel', 'CSV'].includes(text));
            if (found.length || document.querySelector(
                    'button[data-tooltip="Copy to Clipboard"]')) {
                throw new Error(`Export buttons shown: ${found}`);
            }
            console.log('test successful');
        """)
        self.browser_js(
            '/odoo/action-base.action_partner_form?view_type=list', code,
            login='list_view_browser_user')

    def test_04_print_buttons_call_export_routes(self):
        """Verify the PDF, Excel and CSV buttons request their routes and the
        server answers them successfully.
        """
        code = browser_code("""
            await waitFor('.o_list_view .o_data_row');
            const requests = [];
            const open = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function (method, url, ...args) {
                const entry = {url: String(url), status: null};
                requests.push(entry);
                this.addEventListener('loadend', () => { entry.status = this.status; });
                return open.call(this, method, url, ...args);
            };
            const waitForRequest = async (part) => {
                for (let i = 0; i < 150; i++) {
                    const done = requests.find((r) => r.url.includes(part) && r.status);
                    if (done) {
                        if (done.status !== 200) {
                            throw new Error(`${part} answered ${done.status}`);
                        }
                        return done;
                    }
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
                throw new Error(`No request to ${part}: ${requests.map((r) => r.url)}`);
            };
            const click = (text) => [...document.querySelectorAll('.o_control_panel button')]
                .find((button) => button.textContent.trim() === text).click();
            click('Excel');
            await waitForRequest('/web/export/xlsx');
            click('CSV');
            await waitForRequest('/web/export/csv');
            click('PDF');
            await waitForRequest('/get_data');
            await waitForRequest('/report/');
            console.log('test successful');
        """)
        self.browser_js(
            '/odoo/action-base.res_lang_act_window', code, login='admin')

