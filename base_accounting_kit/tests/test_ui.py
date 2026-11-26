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
"""Browser tests of the report screens (headless Chrome). Tagged
``kit_ui`` so they can be skipped where no browser is available:
``--test-tags /base_accounting_kit,-kit_ui``."""
from datetime import date

from odoo import Command, fields
from odoo.tests import HttpCase, tagged

HELPERS = """
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitFor(fn, what) {
    for (let i = 0; i < 100; i++) { const r = fn(); if (r) return r; await sleep(100); }
    throw new Error('Timeout waiting for ' + what);
}
const q = (s) => document.querySelector(s);
const qa = (s) => [...document.querySelectorAll(s)];
const chip = (text) => qa('.o_kit_dr_chip').find((c) => c.textContent.includes(text) || c.title === text);
const item = (text) => qa('.o-dropdown-item, .dropdown-item').find((b) => b.textContent.includes(text));
const rows = () => qa('.o_kit_dr_table tbody tr');
function run(body) {
    (async () => {
        try {
            await waitFor(() => rows().length, 'report table');
            await body();
            console.log('test successful');
        } catch (e) {
            console.error('UI test failed: ' + e.message);
        }
    })();
}
"""

READY = "!!document.querySelector('.o_kit_dynamic_report .o_kit_dr_table')"


def kit_fresh_company(cls, name):
    """Run the class in a new company with the generic chart, as the
    current company of the test env and of ``admin`` in the browser, so
    the tests do not depend on the data already in the database (lock
    dates, bank transactions, open years)."""
    env = cls.env
    company = env['res.company'].create({'name': name, 'currency_id': env.ref('base.USD').id})
    env['account.chart.template'].try_loading('generic_coa', company=company, install_demo=False)
    admin = env.ref('base.user_admin')
    admin.write({'company_ids': [Command.link(company.id)], 'company_id': company.id})
    env.user.write({'company_ids': [Command.link(company.id)], 'company_id': company.id})
    cls.env = env(context=dict(env.context, allowed_company_ids=[company.id]))
    return company


@tagged('post_install', '-at_install', 'kit_ui')
class TestReportScreens(HttpCase):
    """The report screens in the browser: every report opens, unfold and
    fold, search, drill-down, comparison input, saved filters, record chips,
    Review screens."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        company = env.company
        if not env['account.account'].search([('company_ids', 'in', company.id)], limit=1):
            env['account.chart.template'].try_loading('generic_coa', company=company, install_demo=False)
        tax = env['account.tax'].search([('company_id', '=', company.id), ('type_tax_use', '=', 'sale'),
                                         ('amount', '>', 0)], limit=1)
        for name in ('Kit UI Customer', 'Kit UI Other'):
            partner = env['res.partner'].create({'name': name})
            env['account.move'].create({
                'move_type': 'out_invoice', 'partner_id': partner.id, 'invoice_date': fields.Date.today(),
                'invoice_line_ids': [Command.create({'name': 'x', 'quantity': 1, 'price_unit': 100,
                                                     'tax_ids': [Command.set(tax.ids)]})]}).action_post()
        income = env['account.account'].search([('company_ids', 'in', company.id), ('account_type', '=', 'income')], limit=1)
        bank = env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'bank')], limit=1)
        cash = env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'cash')], limit=1) \
            or env['account.journal'].create({'name': 'Kit UI Cash', 'type': 'cash', 'code': 'KUIC'})
        for journal, amount in ((bank, 60), (cash, 40)):
            env['account.move'].create({
                'move_type': 'entry', 'date': fields.Date.today(), 'journal_id': journal.id,
                'line_ids': [Command.create({'account_id': journal.default_account_id.id, 'debit': amount, 'name': 'ui'}),
                             Command.create({'account_id': income.id, 'credit': amount, 'name': 'ui'})]}).action_post()

    def run_js(self, action, body, ready=READY):
        self.browser_js('/odoo/action-base_accounting_kit.%s' % action,
                        HELPERS + 'run(async () => {%s});' % body, ready=ready, login='admin', timeout=120)

    def test_every_report_opens(self):
        """Each report menu opens its screen, named in the breadcrumb."""
        for action, title in (
                ('action_dynamic_profit_loss', 'Profit and Loss'), ('action_dynamic_balance_sheet', 'Balance Sheet'),
                ('action_dynamic_cash_flow', 'Cash Flow Statement'), ('action_dynamic_trial_balance', 'Trial Balance'),
                ('action_dynamic_general_ledger', 'General Ledger'), ('action_dynamic_partner_ledger', 'Partner Ledger'),
                ('action_dynamic_aged_receivable', 'Aged Receivable'), ('action_dynamic_aged_payable', 'Aged Payable'),
                ('action_dynamic_day_book', 'Day Book'), ('action_dynamic_cash_book', 'Cash Book'),
                ('action_dynamic_bank_book', 'Bank Book'), ('action_dynamic_tax', 'Tax Report'),
                ('action_dynamic_journal_audit', 'Journals Audit'),
                ('action_dynamic_bank_reconciliation', 'Bank Reconciliation')):
            with self.subTest(action=action):
                self.run_js(action, """
                    const title = q('.o_last_breadcrumb_item').textContent;
                    if (!title.includes('%s')) throw new Error('title ' + title);
                    if (!q('.o_kit_dr_export [data-icon=download]')) throw new Error('export button');
                    for (const name of ['Options', 'Favorites']) {
                        const label = q('.o_kit_dr_chip[title=' + name + '] .o_kit_dr_chip_label');
                        if (!label || label.textContent.trim() !== name) throw new Error(name + ' label');
                    }
                """ % title)

    def test_unfold_fold_search(self):
        """Unfold / fold a line, the Unfold all chip toggles, search filters
        the lines."""
        self.run_js('action_dynamic_trial_balance', """
            const before = rows().length;
            q('.o_kit_dr_caret').click();
            await waitFor(() => q('.o_kit_dr_child'), 'children');
            if (rows().length <= before) throw new Error('unfold did nothing');
            q('.o_kit_dr_caret').click();
            await sleep(300);
            if (q('.o_kit_dr_child')) throw new Error('fold did nothing');
            chip('Unfold all').click();
            await waitFor(() => qa('.o_kit_dr_child').length >= 2 && chip('Fold all'), 'unfold all');
            chip('Fold all').click();
            await waitFor(() => !q('.o_kit_dr_child'), 'fold all');
            const search = q('.o_kit_dr_search input');
            search.value = 'zzzz-no-match';
            search.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
            await waitFor(() => rows().length === 1, 'only the total row');
        """)

    def test_drill_down(self):
        """A journal item of the General Ledger opens its journal entry."""
        self.run_js('action_dynamic_general_ledger', """
            q('.o_kit_dr_caret').click();
            await waitFor(() => q('.o_kit_dr_child a'), 'journal item');
            q('.o_kit_dr_child a').click();
            await waitFor(() => q('.o_form_view'), 'journal entry form');
        """)

    def test_click_whole_row(self):
        """A click anywhere on a row (here its amount cell) unfolds and folds
        an unfoldable line and opens a drillable one (an account opens the
        General Ledger of that account); plain rows are not clickable."""
        self.run_js('action_dynamic_profit_loss', """
            const section = () => rows().find((r) => r.querySelector('.o_kit_dr_caret'));
            await waitFor(section, 'unfoldable line');
            if (getComputedStyle(section()).cursor !== 'pointer') throw new Error('no pointer');
            const total = rows().find((r) => !r.classList.contains('o_kit_dr_clickable'));
            if (total && getComputedStyle(total).cursor === 'pointer') throw new Error('plain row clickable');
            const before = rows().length;
            section().lastElementChild.click();
            await waitFor(() => rows().length > before, 'unfold from the amount');
            section().lastElementChild.click();
            await waitFor(() => rows().length === before, 'fold from the amount');
            section().lastElementChild.click();
            const account = await waitFor(() => q('.o_kit_dr_child.o_kit_dr_clickable'), 'account line');
            const code = account.firstElementChild.textContent.trim().split(/[ -]/)[0];
            account.lastElementChild.click();
            await waitFor(() => q('.o_last_breadcrumb_item')?.textContent.includes('General Ledger')
                && rows().some((r) => r.classList.contains('o_kit_dr_child'))
                && rows().filter((r) => r.querySelector('.o_kit_dr_caret'))
                    .every((r) => r.textContent.trim().startsWith(code)), 'General Ledger of the account');
            if (!chip('Accounts')?.textContent.includes('1')) throw new Error('accounts filter ' + chip('Accounts')?.textContent);
        """)

    def test_currency_symbol_option(self):
        """Amounts without the currency symbol and "Amounts in <currency>"
        in the header; Options > Currency symbol in amounts adds it back."""
        symbol = self.env.company.currency_id.symbol
        self.run_js('action_dynamic_trial_balance', """
            const amounts = () => qa('.o_kit_dr_table tbody td.text-end').map((td) => td.textContent).join(' ');
            if (amounts().includes('%(symbol)s')) throw new Error('symbol shown: ' + amounts().slice(0, 80));
            if (!q('.o_kit_dr_heading_sub').textContent.includes('Amounts in %(name)s')) throw new Error('unit missing');
            q('.o_kit_dr_chip[title=Options]').click();
            const item = await waitFor(() => qa('.dropdown-item').find((i) => i.textContent.includes('Currency symbol in amounts')), 'option');
            item.click();
            await waitFor(() => amounts().includes('%(symbol)s'), 'symbol back');
            await waitFor(() => !q('.o_kit_dr_heading_sub').textContent.includes('Amounts in'), 'unit gone');
        """ % {'symbol': symbol, 'name': self.env.company.currency_id.name})

    def test_negative_amounts_red(self):
        """Negative amounts are red (with their minus sign), positive ones not."""
        self.run_js('action_dynamic_trial_balance', """
            const cells = qa('.o_kit_dr_table tbody td.text-end').filter((td) => td.textContent.trim());
            const negative = cells.filter((td) => td.textContent.includes('-'));
            if (!negative.length) throw new Error('no negative amount');
            if (!negative.every((td) => td.classList.contains('text-danger'))) throw new Error('negative not red');
            if (cells.some((td) => !td.textContent.includes('-') && td.classList.contains('text-danger')))
                throw new Error('positive shown red');
        """)

    def test_tabular_figures(self):
        """Amounts use tabular (equal-width) digits, so they line up."""
        self.run_js('action_dynamic_trial_balance', """
            const cell = q('.o_kit_dr_table tbody td.text-end');
            const style = getComputedStyle(cell).fontVariantNumeric;
            if (!style.includes('tabular-nums')) throw new Error('digits: ' + style);
        """)

    def test_amount_units(self):
        """The amount unit chip (before the favourites star) shows "In <currency>";
        "In K" adds K to the amounts and becomes the chip label."""
        name = self.env.company.currency_id.name
        self.run_js('action_dynamic_trial_balance', """
            const chip = () => q('.o_kit_dr_amount_unit');
            if (chip().textContent.trim() !== 'In %(name)s') throw new Error('label ' + chip().textContent);
            const star = q('.o_kit_dr_chip[title=Favorites]');
            if (!(chip().compareDocumentPosition(star) & Node.DOCUMENT_POSITION_FOLLOWING)) throw new Error('not before the star');
            chip().click();
            const item = await waitFor(() => qa('.dropdown-item').find((i) => i.textContent.trim() === 'In K %(name)s'), 'K item');
            item.click();
            await waitFor(() => qa('.o_kit_dr_table tbody td.text-end').some((td) => td.textContent.trim().endsWith('K')), 'K amounts');
            await waitFor(() => chip().textContent.trim() === 'In K %(name)s', 'K label');
        """ % {'name': name})

    def test_columns_by_period(self):
        """Compare > By quarter: 4 quarter columns and Total; an amount of an
        account in a quarter opens the General Ledger of that quarter."""
        self.run_js('action_dynamic_profit_loss', """
            const compare = qa('.o_kit_dr_chip').find((c) => c.textContent.includes('Compare'));
            compare.click();
            const item = await waitFor(() => qa('.dropdown-item').find((i) => i.textContent.trim() === 'By quarter'), 'By quarter');
            item.click();
            await waitFor(() => qa('.o_kit_dr_table thead th').length === 6, 'quarter columns');
            if (!compare.textContent.includes('By quarter')) throw new Error('chip ' + compare.textContent);
            const section = rows().find((r) => r.querySelector('.o_kit_dr_caret'));
            section.lastElementChild.click();
            const account = await waitFor(() => q('.o_kit_dr_child.o_kit_dr_clickable'), 'account line');
            const cells = [...account.querySelectorAll('td')].slice(1, 5);
            const cell = cells.find((td) => td.textContent.trim() && td.textContent.trim() !== '0.00') || cells[0];
            cell.click();
            await waitFor(() => q('.o_last_breadcrumb_item')?.textContent.includes('General Ledger'), 'General Ledger');
        """)

    def test_export_menu(self):
        """One Export button with the download icon and PDF, Excel, CSV,
        Print; the print layout hides the control panel."""
        self.run_js('action_dynamic_trial_balance', """
            const button = q('.o_kit_dr_export');
            if (!button.querySelector('[data-icon=download]')) throw new Error('icon');
            const look = getComputedStyle(button);
            const fill = look.backgroundColor.match(/^rgba\(113, 99, 158, ([\d.]+)\)$/);
            if (look.borderTopColor !== 'rgb(113, 99, 158)' || look.color !== 'rgb(113, 99, 158)'
                || !fill || !(parseFloat(fill[1]) > 0 && parseFloat(fill[1]) <= 0.1)) throw new Error('outline ' + look.borderTopColor + ' ' + look.color + ' ' + look.backgroundColor);
            if (qa('.o_control_panel button').some((b) => ['PDF', 'XLSX'].includes(b.textContent.trim()))) throw new Error('old buttons');
            button.click();
            const items = await waitFor(() => qa('.dropdown-item').length >= 4 && qa('.dropdown-item'), 'menu');
            const labels = items.map((i) => i.textContent.trim());
            for (const label of ['PDF', 'Excel (XLSX)', 'CSV', 'Print'])
                if (!labels.includes(label)) throw new Error('missing ' + label + ' in ' + labels);
            const css = [...document.styleSheets].flatMap((s) => { try { return [...s.cssRules]; } catch { return []; } })
                .filter((r) => r.media && r.media.mediaText.includes('print')).map((r) => r.cssText).join(' ');
            if (!css.includes('o_kit_dr_heading')) throw new Error('print css');
        """)

    def test_statement_heading(self):
        """The sheet starts with the report name and, under it, one grey line
        with the period in words and the amount currency, left-aligned with
        the table; no company; Options > Show heading hides it (shown by
        default) and the currency goes back to the table header. The sheet
        takes about 85% of the screen width."""
        name = self.env.company.name
        self.run_js('action_dynamic_balance_sheet', """
            const heading = () => q('.o_kit_dr_heading');
            const text = heading().textContent;
            if (text.includes('%s') || !text.includes('Balance Sheet') || !text.includes('As of')) throw new Error('heading ' + text);
            const title = getComputedStyle(q('.o_kit_dr_heading_title'));
            const sub = getComputedStyle(q('.o_kit_dr_heading_sub'));
            if (parseFloat(title.fontSize) <= parseFloat(sub.fontSize) * 1.3) throw new Error('title size ' + title.fontSize);
            const t = q('.o_kit_dr_heading_title').getBoundingClientRect();
            const s = q('.o_kit_dr_heading_sub').getBoundingClientRect();
            const table = q('.o_kit_dr_table').getBoundingClientRect();
            if (s.top < t.bottom - 1) throw new Error('period not under the title');
            if (Math.abs(t.left - table.left) > 2 || Math.abs(s.left - table.left) > 2) throw new Error('not left-aligned');
            if (!q('.o_kit_dr_heading_sub').textContent.includes('Amounts in')) throw new Error('currency not in heading');
            if (q('.o_kit_dr_unit').textContent.trim()) throw new Error('currency also in the table');
            const content = q('.o_kit_dynamic_report .o_content').clientWidth;
            const ratio = q('.o_kit_dr_sheet').getBoundingClientRect().width / content;
            if (ratio < 0.8 || ratio > 0.97) throw new Error('sheet width ' + ratio.toFixed(2));
            if (getComputedStyle(heading()).display === 'none') throw new Error('hidden by default');
            // main sections on a faint grey band (low opacity)
            const band = getComputedStyle(q('.o_kit_dr_main td')).backgroundColor;
            const [r, g, b, a] = band.match(/[\d.]+/g).map(Number);
            if (!(Math.max(r, g, b) - Math.min(r, g, b) < 30 && a > 0 && a <= 0.1)) throw new Error('main band ' + band);
            q('.o_kit_dr_chip[title=Options]').click();
            const item = await waitFor(() => qa('.dropdown-item').find((i) => i.textContent.includes('Show heading')), 'option');
            item.click();
            await waitFor(() => getComputedStyle(heading()).display === 'none', 'hidden');
            await waitFor(() => q('.o_kit_dr_unit').textContent.includes('Amounts in'), 'currency back in the table');
        """ % name)

    def test_comparison_periods(self):
        """Typing a number of periods in Comparison adds the period and
        variance columns (no error)."""
        self.run_js('action_dynamic_trial_balance', """
            chip('Compare:').click();
            const input = await waitFor(() => q('.o-dropdown--menu input[type=number]'), 'periods input');
            input.value = '3';
            input.dispatchEvent(new Event('change', { bubbles: true }));
            qa('.o-dropdown--menu button').find((b) => b.textContent.includes('Previous periods')).click();
            await waitFor(() => qa('.o_kit_dr_table thead th').length === 10, 'comparison columns');
            if (q('.o_error_dialog')) throw new Error('error dialog');
            if (!chip('Compare:').textContent.includes('Previous (3)')) throw new Error('chip value');
        """)

    def test_saved_filters(self):
        """Save a default filter, reopen the report with it, delete it."""
        self.run_js('action_dynamic_trial_balance', """
            chip('Options').click();
            (await waitFor(() => item('Include draft entries'), 'option')).click();
            await sleep(300);
            chip('Favorites').click();
            const name = await waitFor(() => q('.o-dropdown--menu input[type=text]'), 'name input');
            name.value = 'UI Drafts';
            name.dispatchEvent(new Event('input', { bubbles: true }));
            const box = q('.o-dropdown--menu input[type=checkbox]');
            box.checked = true;
            box.dispatchEvent(new Event('change', { bubbles: true }));
            await sleep(100);
            qa('.o-dropdown--menu button').find((b) => b.textContent.includes('Save')).click();
            await waitFor(() => item('UI Drafts'), 'saved filter');
        """)
        saved = self.env['ir.filters'].search([('name', '=', 'UI Drafts')])
        self.assertTrue(saved.is_default)
        self.run_js('action_dynamic_trial_balance', """
            chip('Options').click();
            const draft = await waitFor(() => item('Include draft entries'), 'option');
            if (draft.querySelector('i').dataset.icon !== 'check') throw new Error('default filter not applied');
            document.body.click();
            await sleep(300);
            chip('Favorites').click();
            const saved = await waitFor(() => item('UI Drafts'), 'saved filter');
            saved.querySelector('[data-icon=delete]').click();
            await waitFor(() => !item('UI Drafts'), 'deleted');
        """)
        self.assertFalse(self.env['ir.filters'].search([('name', '=', 'UI Drafts')]))

    def test_partner_chip(self):
        """Picking a partner in the Partners chip filters the ledger."""
        self.run_js('action_dynamic_partner_ledger', """
            chip('Partners:').click();
            const input = await waitFor(() => q('.o_kit_dr_selector input'), 'selector');
            input.focus();
            input.value = 'Kit UI Customer';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            const option = await waitFor(() => qa('.o-autocomplete--dropdown-item, .o-autocomplete--dropdown-menu li')
                .find((o) => o.textContent.includes('Kit UI Customer')), 'suggestion');
            const target = option.querySelector('a') || option;
            target.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
            target.click();
            await waitFor(() => chip('Partners:').textContent.includes('1 selected'), 'chip value');
            await waitFor(() => !qa('.o_kit_dr_table tbody td').some((t) => t.textContent.includes('Kit UI Other')),
                          'other partner hidden');
        """)

    def test_review_screens(self):
        """Review > To Review list screens open."""
        js = """
            const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
            (async () => {
                for (let i = 0; i < 100 && !document.querySelector('%s'); i++) await sleep(100);
                if (document.querySelector('%s') && !document.querySelector('.o_error_dialog')) console.log('test successful');
                else console.error('UI test failed: screen not shown');
            })();
        """
        for action, selector in (('action_review_entries', '.o_list_view'),
                                 ('action_review_draft_entries', '.o_list_view')):
            with self.subTest(action=action):
                self.browser_js('/odoo/action-base_accounting_kit.%s' % action, js % (selector, selector),
                                ready="!!document.querySelector('.o_view_controller')", login='admin', timeout=60)


REC_HELPERS = """
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitFor(fn, what) {
    for (let i = 0; i < 100; i++) { const r = fn(); if (r) return r; await sleep(100); }
    throw new Error('Timeout waiting for ' + what);
}
const q = (s) => document.querySelector(s);
const qa = (s) => [...document.querySelectorAll(s)];
const row = (text) => qa('.o_kit_rec_row').find((r) => r.textContent.includes(text));
const tab = (text) => qa('.o_kit_rec_drawer .nav-link').find((b) => b.textContent.includes(text));
function run(body) {
    (async () => {
        try {
            await waitFor(() => q('.o_kit_rec_table, .o_kit_rec_card, .o_kit_rec_empty'), 'reconciliation screen');
            await body();
            console.log('test successful');
        } catch (e) {
            console.error('UI test failed: ' + e.message);
        }
    })();
}
"""


@tagged('post_install', '-at_install', 'kit_ui')
class TestReconciliationScreen(HttpCase):
    """The reconciliation screen in the browser: groups, accept all sure,
    the drawer with suggestions, search entries and models, preview and
    validation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = kit_fresh_company(cls, 'Kit UI Reconciliation')
        env = cls.env
        cls.bank = env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'bank')], limit=1)
        today = fields.Date.today()
        partner = env['res.partner'].create({'name': 'Kit Rec Customer'})
        invoices = env['account.move'].create([{
            'move_type': 'out_invoice', 'partner_id': partner.id, 'invoice_date': today,
            'invoice_line_ids': [Command.create({'name': 'x', 'quantity': 1, 'price_unit': amount, 'tax_ids': False})]}
            for amount in (300, 120, 80)])
        invoices.action_post()
        fees = env['account.account'].search([('company_ids', 'in', company.id), ('account_type', '=', 'expense')], limit=1)
        env['account.reconcile.model'].create({'name': 'Kit UI fees', 'line_ids': [Command.create({'account_id': fees.id})]})
        lines = [('Payment %s' % invoices[0].name, 300, False), ('Kit UI open item', 200, partner.id),
                 ('Kit UI card fee', -9, False)]
        env['account.bank.statement.line'].create([{
            'journal_id': cls.bank.id, 'date': today, 'payment_ref': label, 'amount': amount, 'partner_id': partner_id}
            for label, amount, partner_id in lines])

    def run_js(self, body):
        self.browser_js('/odoo/action-base_accounting_kit.action_kit_bank_reconciliation',
                        REC_HELPERS + 'run(async () => {%s});' % body,
                        ready="!!document.querySelector('.o_kit_bank_rec')", login='admin', timeout=120)

    def test_accept_and_drawer(self):
        """Accept all sure reconciles the invoice named in the label; the
        drawer preselects the two invoices that add up, shows the preview
        and validates; Validate stays disabled until something is chosen;
        a model books the card fee."""
        self.run_js("""
            if (!q('.o_kit_rec_accept_all')) throw new Error('no sure group');
            q('.o_kit_rec_accept_all').click();
            await waitFor(() => !q('.o_kit_rec_accept_all'), 'sure lines reconciled');
            row('Kit UI open item').click();
            await waitFor(() => qa('.o_kit_rec_drawer .o_kit_rec_item_on').length === 2, 'preselected items');
            await waitFor(() => qa('.o_kit_rec_preview tbody tr').length === 3 && !q('.o_kit_rec_validate').disabled, 'entry preview');
            q('.o_kit_rec_validate').click();
            await waitFor(() => !row('Kit UI open item'), 'validated');
            row('Kit UI card fee').click();
            await waitFor(() => q('.o_kit_rec_drawer_head')?.textContent.includes('Kit UI card fee') && tab('Models'), 'drawer');
            tab('Models').click();
            if (!q('.o_kit_rec_validate').disabled) throw new Error('Validate enabled with nothing chosen');
            (await waitFor(() => q('.o_kit_rec_model'), 'model')).click();
            await waitFor(() => !q('.o_kit_rec_validate').disabled
                && qa('.o_kit_rec_preview tbody tr').some((tr) => tr.textContent.includes('fee') || !tr.textContent.includes('Suspense')), 'model chosen');
            q('.o_kit_rec_validate').click();
            // Only the test's own lines: databases with demo data keep other open transactions.
            await waitFor(() => !row('Kit UI card fee'), 'card fee booked');
            if (q('.o_error_dialog')) throw new Error('error dialog');
        """)
        self.assertFalse(self.env['account.bank.statement.line'].search(
            [('journal_id', '=', self.bank.id), ('payment_ref', 'like', 'Kit UI'), ('is_reconciled', '=', False)]))

    def test_search_entries_and_tabs(self):
        """Cards by default and the Cards / List switch; Search entries
        finds an open item and ticking it updates the difference; Book to
        account shows Odoo's account field."""
        self.run_js("""
            if (!q('.o_kit_rec_card')) throw new Error('cards are not the default');
            const view = (name) => qa('.o_kit_rec_view_switch button').find((b) => b.textContent.includes(name));
            view('List').click();
            await waitFor(() => q('.o_kit_rec_table') && !q('.o_kit_rec_card'), 'list view');
            view('Cards').click();
            await waitFor(() => q('.o_kit_rec_card'), 'cards view');
            row('Kit UI card fee').click();
            await waitFor(() => tab('Search entries'), 'drawer');
            tab('Search entries').click();
            const input = await waitFor(() => q('.o_kit_rec_entry_search input'), 'search input');
            input.value = 'INV';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
            const item = await waitFor(() => q('.o_kit_rec_drawer .o_kit_rec_item input[type=checkbox]'), 'search result');
            const before = q('.o_kit_rec_difference').textContent;
            item.click();
            await waitFor(() => q('.o_kit_rec_difference').textContent !== before, 'difference updated');
            tab('Book to account').click();
            await waitFor(() => q('.o_kit_rec_account_grid .o_field_many2one'), 'account field');
            document.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
            await waitFor(() => !q('.o_kit_rec_drawer'), 'drawer closed');
        """)


@tagged('post_install', '-at_install', 'kit_ui')
class TestOpenItemsScreen(HttpCase):
    """Open Items mode in the browser: partners with debits and credits,
    accept all sure, the two-column drawer with Select all and Reconcile."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        company = env.company
        if not env['account.account'].search([('company_ids', 'in', company.id)], limit=1):
            env['account.chart.template'].try_loading('generic_coa', company=company, install_demo=False)
        today = fields.Date.today()
        bank = env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'bank')], limit=1)
        misc = env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'general')], limit=1)

        def invoice(partner, amount):
            move = env['account.move'].create({
                'move_type': 'out_invoice', 'partner_id': partner.id, 'invoice_date': today,
                'invoice_line_ids': [Command.create({'name': 'x', 'quantity': 1, 'price_unit': amount, 'tax_ids': False})]})
            move.action_post()
            return move

        def payment(partner, amount, ref, account):
            env['account.move'].create({
                'move_type': 'entry', 'journal_id': misc.id, 'date': today, 'ref': ref,
                'line_ids': [Command.create({'account_id': bank.default_account_id.id, 'debit': amount, 'name': ref}),
                             Command.create({'account_id': account.id, 'credit': amount, 'partner_id': partner.id,
                                             'name': ref})]}).action_post()
        sure, partial = env['res.partner'].create([{'name': 'Kit UI Sure Co'}, {'name': 'Kit UI Partial Co'}])
        inv = invoice(sure, 200)
        receivable = inv.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable').account_id
        payment(sure, 200, 'Payment %s' % inv.name, receivable)
        invoice(partial, 100)
        invoice(partial, 50)
        payment(partial, 140, 'Cheque 77', receivable)

    def test_open_items(self):
        """Accept all sure clears the sure partner; Select all and Reconcile
        (keeping the rest open) clears the other one."""
        self.browser_js('/odoo/action-base_accounting_kit.action_kit_open_items', REC_HELPERS + """run(async () => {
            if (!q('.o_kit_rec_mode_switch .btn-primary').textContent.includes('Open items')) throw new Error('mode');
            await waitFor(() => row('Kit UI Sure Co') && row('Kit UI Partial Co'), 'partner rows');
            q('.o_kit_rec_accept_all').click();
            await waitFor(() => !row('Kit UI Sure Co'), 'sure partner matched');
            row('Kit UI Partial Co').click();
            await waitFor(() => qa('.o_kit_rec_select_all').length === 2, 'open items drawer');
            qa('.o_kit_rec_select_all').forEach((link) => link.click());
            await waitFor(() => q('.o_kit_rec_difference').textContent.includes('10'), 'difference');
            await waitFor(() => !q('.o_kit_rec_validate').disabled, 'reconcile enabled');
            q('.o_kit_rec_validate').click();
            await waitFor(() => !row('Kit UI Partial Co'), 'partner matched');
            if (q('.o_error_dialog')) throw new Error('error dialog');
        });""", ready="!!document.querySelector('.o_kit_bank_rec')", login='admin', timeout=120)
        partial = self.env['res.partner'].search([('name', '=', 'Kit UI Partial Co')])
        invoices = self.env['account.move'].search([('partner_id', '=', partial.id), ('move_type', '=', 'out_invoice')])
        self.assertAlmostEqual(sum(invoices.mapped('amount_residual')), 10)


@tagged('post_install', '-at_install', 'kit_ui')
class TestStatementImportWizard(HttpCase):
    """Import Statement in the browser (P2.2): upload a CSV with unknown
    columns, say which column holds what, import, format saved."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        company = env.company
        if not env['account.account'].search([('company_ids', 'in', company.id)], limit=1):
            env['account.chart.template'].try_loading('generic_coa', company=company, install_demo=False)
        cls.bank = env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'bank')])
        cls.bank[1:].active = False

    def test_set_columns(self):
        js = """
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitFor(fn, what) {
    for (let i = 0; i < 100; i++) { const r = fn(); if (r) return r; await sleep(100); }
    throw new Error('Timeout waiting for ' + what);
}
const q = (s) => document.querySelector(s);
const qa = (s) => [...document.querySelectorAll(s)];
async function choose(field, text) {
    field.querySelector('.o_select_menu_toggler').click();
    const item = await waitFor(() => qa('.o_select_menu_item').find((i) => i.textContent.trim() === text),
                               'option ' + text);
    item.click();
    await waitFor(() => !q('.o_select_menu_item'), 'menu closed');
}
(async () => {
    try {
        const button = await waitFor(() => qa('.o_list_buttons button, .o_control_panel button')
            .find((b) => b.textContent.includes('Import Statement')), 'import button');
        button.click();
        const input = await waitFor(() => q('.modal .o_field_many2many_binary input[type=file]'), 'file input');
        const csv = 'Booked;Text;In;Out\\n2026-04-05;Salary;2500,00;\\n2026-04-06;Shop;;19,90\\n';
        const transfer = new DataTransfer();
        transfer.items.add(new File([csv], 'kit_ui_bank.csv', { type: 'text/csv' }));
        input.files = transfer.files;
        input.dispatchEvent(new Event('change', { bubbles: true }));
        await waitFor(() => q('.modal .o_field_many2many_binary').textContent.includes('kit_ui_bank'), 'file uploaded');
        q('.modal button[name=action_statement_import]').click();
        await waitFor(() => qa('.modal div[name=column_ids] .o_data_row').length === 4, 'columns step');
        const holds = ['Date', 'Label', 'Money in', 'Money out'];
        for (let i = 0; i < 4; i++) {
            qa('.modal div[name=column_ids] .o_data_row')[i].querySelector('td[name=field]').click();
            const cell = await waitFor(() => {
                const td = qa('.modal div[name=column_ids] .o_data_row')[i].querySelector('td[name=field]');
                return td.querySelector('.o_select_menu_toggler') && td;
            }, 'column menu ' + i);
            await choose(cell, holds[i]);
        }
        await choose(q('.modal div[name=decimal_separator]'), 'Comma (1.234,56)');
        await sleep(200);
        q('.modal button[name=action_statement_import]').click();
        await waitFor(() => !q('.modal') && q('.o_form_view div[name=balance_end_real]'), 'statement form');
        if (q('.o_error_dialog')) throw new Error('error dialog');
        console.log('test successful');
    } catch (e) {
        console.error('UI test failed: ' + e.message);
    }
})();
"""
        self.browser_js('/odoo/action-account.action_bank_statement_tree', js,
                        ready="!!document.querySelector('.o_list_view')", login='admin', timeout=120)
        statement = self.env['account.bank.statement'].search([('name', '=', 'kit_ui_bank')])
        self.assertEqual(sorted(statement.line_ids.mapped('amount')), [-19.9, 2500])
        fmt = self.env['kit.statement.import.map'].search([('journal_id', '=', self.bank[:1].id)])
        self.assertEqual((fmt.date_column, fmt.label_column, fmt.decimal_separator), ('Booked', 'Text', 'comma'))
        self.assertEqual(statement.attachment_ids.name, 'kit_ui_bank.csv')


@tagged('post_install', '-at_install', 'kit_ui')
class TestClosingScreens(HttpCase):
    """P2.3-a in the browser: Lock Dates shows the five dates; a lock
    exception is created from Accounting > Closing > Lock Exceptions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        kit_fresh_company(cls, 'Kit UI Closing')

    JS = """
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitFor(fn, what) {
    for (let i = 0; i < 100; i++) { const r = fn(); if (r) return r; await sleep(100); }
    throw new Error('Timeout waiting for ' + what);
}
const q = (s) => document.querySelector(s);
const qa = (s) => [...document.querySelectorAll(s)];
(async () => {
    try {
        %s
        if (q('.o_error_dialog')) throw new Error('error dialog');
        console.log('test successful');
    } catch (e) {
        console.error('UI test failed: ' + e.message);
    }
})();
"""

    def test_lock_dates_dialog(self):
        """The Lock Dates dialog has the five core lock dates."""
        self.browser_js('/odoo/action-base_accounting_kit.account_update_lock_date_act_window', self.JS % """
            await waitFor(() => q('.modal div[name=hard_lock_date]'), 'lock dates dialog');
            for (const name of ['fiscalyear_lock_date', 'tax_lock_date', 'sale_lock_date', 'purchase_lock_date']) {
                if (!q('.modal div[name=' + name + ']')) throw new Error('missing ' + name);
            }
        """, ready="!!document.querySelector('.o_web_client')", login='admin', timeout=120)

    def test_create_lock_exception(self):
        """New exception: lock date, reason, save; it shows as Active."""
        self.env.company.fiscalyear_lock_date = '2020-12-31'
        self.browser_js('/odoo/action-base_accounting_kit.action_kit_lock_exceptions', self.JS % """
            const button = await waitFor(() => q('.o_list_button_add'), 'New button');
            button.click();
            const field = await waitFor(() => q('.o_form_view div[name=lock_date_field]'), 'form');
            field.querySelector('.o_select_menu_toggler, select').click();
            const option = await waitFor(() => qa('.o_select_menu_item').find((i) => i.textContent.includes('Global Lock Date')), 'option');
            option.click();
            await waitFor(() => q('.o_form_view div[name=kit_company_lock_date]')?.textContent.includes('2020'), 'current lock date');
            const reason = q('.o_form_view div[name=reason] input');
            reason.value = 'Kit UI correction';
            reason.dispatchEvent(new Event('input', { bubbles: true }));
            reason.dispatchEvent(new Event('change', { bubbles: true }));
            q('.o_form_view button[name=action_kit_create]').click();
            await waitFor(() => q('.o_form_view .o_statusbar_status .o_arrow_button_current')?.textContent.includes('Active'), 'saved active');
        """, ready="!!document.querySelector('.o_list_view')", login='admin', timeout=120)
        exception = self.env['account.lock_exception'].search([('reason', '=', 'Kit UI correction')])
        self.assertEqual(exception.lock_date_field, 'fiscalyear_lock_date')
        self.assertEqual(str(exception.company_lock_date), '2020-12-31')

    def test_fiscal_year_close(self):
        """Fiscal Years: Create Next Year opens the new year; Close Year
        opens the Year-end Closing (result 500) and closes it with its
        closing entry. (Old years: the demo bank transactions of
        this year would block the Global Lock Date, as core checks.)"""
        old = self.env['kit.fiscal.year'].create({
            'date_from': date(date.today().year - 10, 1, 1), 'date_to': date(date.today().year - 10, 12, 31)})
        old._close()
        company = self.env.company
        Account = self.env['account.account']
        income = Account.search([('company_ids', 'in', company.id), ('account_type', '=', 'income')], limit=1)
        current = Account.search([('company_ids', 'in', company.id), ('account_type', '=', 'asset_current')], limit=1)
        company.kit_retained_earnings_account_id = Account.search(
            [('company_ids', 'in', company.id), ('account_type', '=', 'equity')], limit=1)
        self.env['account.move'].create({
            'move_type': 'entry', 'date': date(date.today().year - 9, 6, 30),
            'line_ids': [Command.create({'account_id': current.id, 'debit': 500, 'name': 'ui'}),
                         Command.create({'account_id': income.id, 'credit': 500, 'name': 'ui'})]}).action_post()
        self.browser_js('/odoo/action-base_accounting_kit.action_kit_fiscal_year', self.JS % """
            const create = await waitFor(() => qa('.o_control_panel button, .o_list_buttons button')
                .find((b) => b.textContent.includes('Create Next Year')), 'Create Next Year');
            create.click();
            const close = await waitFor(() => q('.o_form_view button[name=action_close]'), 'year form');
            close.click();
            const wizard = await waitFor(() => q('.modal button[name=action_close]'), 'year-end closing');
            if (!q('.modal div[name=result]').textContent.includes('500')) throw new Error('result ' + q('.modal div[name=result]').textContent);
            wizard.click();
            await waitFor(() => q('.o_form_view button[name=action_reopen]'), 'closed year');
            await waitFor(() => q('.o_form_view button[name=action_open_closing_move]'), 'closing entry button');
        """, ready="!!document.querySelector('.o_list_view, .o_view_nocontent')", login='admin', timeout=120)
        year = self.env['kit.fiscal.year'].search([('company_id', '=', self.env.company.id)], order='date_to desc', limit=1)
        self.assertEqual(year.date_from.year, date.today().year - 9)
        self.assertEqual(year.state, 'closed')
        self.assertEqual(self.env.company.fiscalyear_lock_date, year.date_to)
        self.assertEqual(year.closing_move_id.amount_total, 500)

    def test_month_end_closing(self):
        """Month-end Closing: Start Next Month copies the tasks; Done on the
        task; Close Month closes and locks the month."""
        Closing = self.env['kit.period.closing']
        self.env['kit.closing.task.template'].create({'name': 'Kit UI accruals', 'user_id': self.env.ref('base.user_admin').id})
        first = Closing._start_month(self.env.company, date(date.today().year - 10, 1, 1))
        first.task_ids.action_done()
        first.action_close()
        self.browser_js('/odoo/action-base_accounting_kit.action_kit_period_closing', self.JS % """
            const start = await waitFor(() => qa('.o_control_panel button, .o_list_buttons button')
                .find((b) => b.textContent.includes('Start Next Month')), 'Start Next Month');
            start.click();
            const done = await waitFor(() => q('.o_form_view div[name=task_ids] button[name=action_done]'), 'task row');
            done.click();
            await waitFor(() => q('.o_form_view div[name=task_ids] button[name=action_undo]'), 'task done');
            q('.o_form_view button[name=action_close]').click();
            await waitFor(() => q('.o_form_view button[name=action_reopen]'), 'closed month');
        """, ready="!!document.querySelector('.o_list_view, .o_view_nocontent')", login='admin', timeout=120)
        february = Closing.search([('company_id', '=', self.env.company.id)], order='date_from desc', limit=1)
        self.assertEqual((february.date_from.month, february.state), (2, 'closed'))
        self.assertTrue(february.task_ids.done)
        self.assertEqual(self.env.company.fiscalyear_lock_date, february.date_to)
