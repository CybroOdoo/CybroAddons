import io

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountDayBookReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Day Book Partner',
        })
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'general'),
        ], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Day Book Miscellaneous Journal',
                'code': 'TDB',
                'type': 'general',
            })
        cls.debit_account = cls.env['account.account'].create({
            'name': 'Day Book Debit Account',
            'code': 'TDB100',
            'account_type': 'asset_current',
        })
        cls.credit_account = cls.env['account.account'].create({
            'name': 'Day Book Credit Account',
            'code': 'TDB200',
            'account_type': 'income',
        })
        cls.posted_move = cls._create_move('2026-01-15', post=True)
        cls.draft_move = cls._create_move('2026-01-16', post=False)

    @classmethod
    def _create_move(cls, move_date, post=False):
        move = cls.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': cls.journal.id,
            'date': move_date,
            'line_ids': [
                (0, 0, {
                    'name': 'Day Book Debit Line',
                    'account_id': cls.debit_account.id,
                    'partner_id': cls.partner.id,
                    'debit': 100.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Day Book Credit Line',
                    'account_id': cls.credit_account.id,
                    'partner_id': cls.partner.id,
                    'debit': 0.0,
                    'credit': 100.0,
                }),
            ],
        })
        if post:
            move.action_post()
        return move

    def _create_wizard(self, **values):
        vals = {
            'date_from': '2026-01-01',
            'date_to': '2026-01-31',
            'target_move': 'posted',
            'account_ids': [(6, 0, [self.debit_account.id])],
            'journal_ids': [(6, 0, [self.journal.id])],
        }
        vals.update(values)
        return self.env['account.day.book.report'].create(vals)

    def _form_data(self, target_move='posted', date_from='2026-01-01',
                   date_to='2026-01-31'):
        return {
            'date_from': date_from,
            'date_to': date_to,
            'target_move': target_move,
            'account_ids': [self.debit_account.id],
            'journal_ids': [self.journal.id],
        }

    def test_check_date_rejects_start_date_after_end_date(self):
        with self.assertRaises(ValidationError):
            self._create_wizard(
                date_from='2026-02-01',
                date_to='2026-01-01',
            )

    def test_report_xlsx_returns_download_action(self):
        wizard = self._create_wizard()

        action = wizard.report_xlsx()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'day_xlsx_download')
        self.assertEqual(action['data']['model'], 'account.day.book.report')
        self.assertEqual(action['data']['output_format'], 'xlsx')
        self.assertEqual(action['data']['report_name'], 'Day Book')

    def test_get_account_move_entry_returns_posted_lines_only(self):
        wizard = self._create_wizard()

        lines = wizard._get_account_move_entry(
            self.debit_account,
            self._form_data(target_move='posted'),
        )

        line_ids = [line['lid'] for line in lines]
        self.assertIn(
            self.posted_move.line_ids.filtered(
                lambda line: line.account_id == self.debit_account
            ).id,
            line_ids,
        )
        self.assertNotIn(
            self.draft_move.line_ids.filtered(
                lambda line: line.account_id == self.debit_account
            ).id,
            line_ids,
        )

    def test_get_account_move_entry_can_include_draft_lines(self):
        wizard = self._create_wizard(target_move='all')

        lines = wizard._get_account_move_entry(
            self.debit_account,
            self._form_data(target_move='all'),
        )

        line_ids = [line['lid'] for line in lines]
        self.assertIn(
            self.draft_move.line_ids.filtered(
                lambda line: line.account_id == self.debit_account
            ).id,
            line_ids,
        )

    def test_check_report_raises_when_no_lines_match(self):
        wizard = self._create_wizard(
            date_from='1999-01-01',
            date_to='1999-01-31',
        )

        with self.assertRaises(ValidationError):
            wizard.check_report()

    def test_get_xlsx_report_writes_workbook_content(self):
        wizard = self._create_wizard()
        response = type('Response', (), {'stream': io.BytesIO()})()

        wizard.get_xlsx_report({'form': self._form_data()}, response)

        self.assertTrue(response.stream.getvalue().startswith(b'PK'))

    def test_get_xlsx_report_raises_when_no_lines_match(self):
        wizard = self._create_wizard()
        response = type('Response', (), {'stream': io.BytesIO()})()
        options = {
            'form': self._form_data(
                date_from='1999-01-01',
                date_to='1999-01-31',
            )
        }

        with self.assertRaises(ValidationError):
            wizard.get_xlsx_report(options, response)
