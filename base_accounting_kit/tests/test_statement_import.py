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
import base64
import io
from datetime import date

import openpyxl

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import file_open

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestStatementImport(AccountingKitTestCommon):
    """Bank statement import (P1.10, P2.2): one statement per file, amounts
    and balances, duplicate check, CSV / XLSX / OFX / QIF / CAMT / MT940,
    saved column formats, account and currency checks, several files, clear
    errors, entry points on bank, cash and credit card journals."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acme = cls.env['res.partner'].create({'name': 'Kit Bank Acme'})
        cls.journal_count = 0

    def bank_journal(self, journal_type='bank', account=None):
        type(self).journal_count += 1
        vals = {'name': 'Kit Import %s' % self.journal_count, 'type': journal_type,
                'code': 'KI%s' % self.journal_count}
        if account:
            vals['bank_account_id'] = self.env['res.partner.bank'].create({
                'account_number': account, 'partner_id': self.company.partner_id.id}).id
        return self.env['account.journal'].create(vals)

    def run_import(self, journal, name, content):
        data = content.encode() if isinstance(content, str) else content
        wizard = self.env['import.bank.statement'].create({
            'attachment': base64.b64encode(data).decode(), 'file_name': name,
            'journal_id': journal.id if journal else False})
        return wizard.action_statement_import()

    def attachments(self, files):
        return self.env['ir.attachment'].create([
            {'name': name, 'raw': content.encode() if isinstance(content, str) else content}
            for name, content in files])

    @staticmethod
    def sample(name):
        with file_open('base_accounting_kit/static/src/sample/%s' % name, 'rb') as sample:
            return sample.read()

    def import_error(self, journal, name, content):
        with self.assertRaises(UserError) as error:
            self.run_import(journal, name, content)
        return str(error.exception)

    def statements(self, journal):
        return self.env['account.bank.statement'].search([('journal_id', '=', journal.id)], order='id')

    @staticmethod
    def xlsx(rows):
        workbook = openpyxl.Workbook()
        for row in rows:
            workbook.active.append(row)
        out = io.BytesIO()
        workbook.save(out)
        return out.getvalue()

    @staticmethod
    def ofx(currency, transactions, balance):
        body = ''.join('<STMTTRN><TRNTYPE>%s<DTPOSTED>%s<TRNAMT>%s<FITID>%s<NAME>%s<MEMO>%s</STMTTRN>\n' % (
            'CREDIT' if float(amount) > 0 else 'DEBIT', day, amount, fitid, name, memo)
            for day, amount, fitid, name, memo in transactions)
        return ("OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\nCHARSET:1252\n"
                "COMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n\n<OFX>\n<SIGNONMSGSRSV1><SONRS><STATUS><CODE>0"
                "<SEVERITY>INFO</STATUS><DTSERVER>20260310<LANGUAGE>ENG</SONRS></SIGNONMSGSRSV1>\n<BANKMSGSRSV1>"
                "<STMTTRNRS><TRNUID>1<STATUS><CODE>0<SEVERITY>INFO</STATUS>\n<STMTRS><CURDEF>%s<BANKACCTFROM>"
                "<BANKID>123<ACCTID>456<ACCTTYPE>CHECKING</BANKACCTFROM>\n<BANKTRANLIST><DTSTART>20260301"
                "<DTEND>20260310\n%s</BANKTRANLIST>\n<LEDGERBAL><BALAMT>%s<DTASOF>20260310</LEDGERBAL>\n"
                "</STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>\n") % (currency, body, balance)

    # ------------------------------------------------------------------
    def test_csv_and_duplicates(self):
        """CSV with running balance: one statement, amounts kept, balances
        from the file, partners matched or kept as names, identical lines
        both imported; re-import skips what is already there."""
        journal = self.bank_journal()
        csv = ("date,label,partner,amount,balance\n"
               "2026-03-01,Deposit,%s,1000,1500\n"
               "2026-03-02,Coffee,Unknown Shop,-5,1495\n"
               "2026-03-02,Coffee,Unknown Shop,-5,1490\n") % self.acme.name
        action = self.run_import(journal, 'march.csv', csv)
        statement = self.statements(journal)
        self.assertEqual(len(statement.line_ids), 3)
        self.assertEqual(sorted(statement.line_ids.mapped('amount')), [-5, -5, 1000])
        self.assertAmount(statement.balance_end_real, 1490)
        self.assertAmount(statement.balance_start, 500)
        self.assertTrue(statement.is_complete)
        self.assertEqual(statement.name, 'march')
        self.assertEqual(action.get('res_id'), statement.id)
        self.assertEqual(statement.line_ids.filtered(lambda l: l.amount == 1000).partner_id, self.acme)
        unknown = statement.line_ids.filtered(lambda l: l.amount == -5)[:1]
        self.assertEqual((unknown.partner_id, unknown.partner_name), (self.env['res.partner'], 'Unknown Shop'))
        self.assertIn('already imported', self.import_error(journal, 'march.csv', csv))
        action = self.run_import(journal, 'march2.csv', csv + "2026-03-03,Rent,,-400,1090\n")
        second = self.statements(journal)[-1:]
        self.assertEqual(second.line_ids.mapped('amount'), [-400])
        self.assertIn('1 imported, 3 already there', action['params']['message'])
        self.assertAmount(second.balance_start, 1490)
        self.assertAmount(second.balance_end_real, 1090)

    def test_csv_shapes_and_errors(self):
        """Semicolon / debit-credit files, balances continued from the
        previous statement, clear errors for empty files, bad dates or
        amounts, missing amount column and unknown file types."""
        journal = self.bank_journal()
        self.run_import(journal, 'dc.csv', "Date;Description;Debit;Credit\n05/03/2026;Salary;;2500\n06/03/2026;Shop;120.50;\n")
        statement = self.statements(journal)
        self.assertEqual(sorted(statement.line_ids.mapped('amount')), [-120.5, 2500])
        self.assertAmount(statement.balance_end_real, 2379.5)
        self.run_import(journal, 'dc2.csv', "date,label,amount\n2026-03-10,Fee,-9.5\n")
        statement = self.statements(journal)[-1:]
        self.assertAmount(statement.balance_start, 2379.5)
        self.assertAmount(statement.balance_end_real, 2370)
        self.assertIn('no transactions', self.import_error(journal, 'e.csv', "date,label,amount\n"))
        self.assertIn('no transactions', self.import_error(journal, 'e0.csv', ""))
        error = self.import_error(journal, 'bad.csv', "date,label,amount\n31-31-2026,X,5\n")
        self.assertIn('Row 2', error)
        error = self.import_error(journal, 'bad2.csv', "date,label,amount\n2026-03-01,X,abc\n")
        self.assertIn('amount', error)
        # Unknown columns: the wizard asks which column holds what.
        self.assertEqual(self.run_import(journal, 'noamt.csv', "date,label,ref\n2026-03-01,X,R1\n")['res_model'],
                         'import.bank.statement')
        self.assertIn('CAMT (XML), MT940, CSV, XLSX, OFX or QIF', self.import_error(journal, 'x.txt', 'abc'))

    def test_xlsx(self):
        """XLSX with headers, and the older column layout."""
        journal = self.bank_journal()
        self.run_import(journal, 'h.xlsx', self.xlsx([['Date', 'Label', 'Amount'], [date(2026, 3, 1), 'A', 100],
                                                      [date(2026, 3, 2), 'B', -30]]))
        self.assertEqual(sorted(self.statements(journal).line_ids.mapped('amount')), [-30, 100])
        self.run_import(journal, 'old.xlsx', self.xlsx([['Name', 'Amount', 'Date', 'Partner'],
                                                        ['Pay 1', 50, '2026-03-05', self.acme.name],
                                                        ['Pay 2', -20, '2026-03-06', None]]))
        statement = self.statements(journal)[-1:]
        self.assertEqual(sorted(statement.line_ids.mapped('amount')), [-20, 50])
        self.assertEqual(statement.line_ids.filtered(lambda l: l.amount == 50).partner_id, self.acme)

    def test_ofx(self):
        """OFX: balances from the ledger balance, duplicates by FITID,
        overlapping files, other currency refused."""
        journal = self.bank_journal()
        currency = self.company.currency_id.name
        first = self.ofx(currency, [('20260305', '200.00', 'F1', 'Client A', 'Invoice 1'),
                                    ('20260306', '-50.00', 'F2', 'Shop', 'Supplies')], '2150.00')
        self.run_import(journal, 'bank.ofx', first)
        statement = self.statements(journal)
        self.assertEqual(sorted(statement.line_ids.mapped('amount')), [-50, 200])
        self.assertAmount(statement.balance_end_real, 2150)
        self.assertAmount(statement.balance_start, 2000)
        self.assertIn('already imported', self.import_error(journal, 'bank.ofx', first))
        second = self.ofx(currency, [('20260306', '-50.00', 'F2', 'Shop', 'Supplies'),
                                     ('20260308', '75.00', 'F3', 'Client B', 'Invoice 2')], '2225.00')
        self.run_import(journal, 'bank2.ofx', second)
        statement = self.statements(journal)[-1:]
        self.assertEqual(statement.line_ids.mapped('amount'), [75])
        self.assertAmount(statement.balance_start, 2150)
        other = 'EUR' if currency != 'EUR' else 'USD'
        error = self.import_error(journal, 'other.ofx', self.ofx(other, [('20260309', '10.00', 'F9', 'X', 'Y')], '10.00'))
        self.assertIn(other, error)

    def test_qif(self):
        """QIF without account header and with !Account / Windows line
        endings."""
        journal = self.bank_journal()
        self.run_import(journal, 'a.qif', "!Type:Bank\nD03/05/2026\nT100.00\nPCustomer Q\n^\nD03/06/2026\nT-20.00\nPShop\n^\n")
        self.assertEqual(sorted(self.statements(journal).line_ids.mapped('amount')), [-20, 100])
        self.run_import(journal, 'b.qif', "!Account\nNChecking\nTBank\n^\n!Type:Bank\r\nD03/07/2026\r\nT55.00\r\nPClient R\r\n^\r\n")
        self.assertEqual(self.statements(journal)[-1:].line_ids.mapped('amount'), [55])

    def test_entry_points(self):
        """The import is offered on bank, cash and credit card journals and
        on the statements list; the sample CSV imports."""
        kanban = self.env['account.journal'].get_view(
            self.env.ref('account.account_journal_dashboard_kanban_view').id, 'kanban')['arch']
        self.assertIn("['bank', 'cash', 'credit'].includes(journal_type)", kanban)
        self.assertIn('Import Statement', kanban)
        statements = self.env['account.bank.statement'].get_view(
            self.env.ref('account.view_bank_statement_tree').id, 'list')['arch']
        self.assertIn('Import Statement', statements)
        cash = self.bank_journal('cash')
        action = cash.action_import_wizard()
        self.assertEqual(action['context']['default_journal_id'], cash.id)
        with file_open('base_accounting_kit/static/src/sample/bank_statement_sample.csv', 'rb') as sample:
            self.run_import(cash, 'bank_statement_sample.csv', sample.read())
        statement = self.statements(cash)
        self.assertEqual(len(statement.line_ids), 3)
        self.assertAmount(statement.balance_end_real, 1449.10)
        credit = self.bank_journal('credit')
        self.run_import(credit, 'card.csv', "date,label,amount\n2026-03-01,Fuel,-60\n")
        self.assertEqual(len(self.statements(credit)), 1)

    # ------------------------------------------------------------------
    # P2.2: bank formats, saved formats, journal checks, several files
    # ------------------------------------------------------------------
    IBAN = 'BE68539007547034'
    CUSTOMER_IBAN = 'DE89370400440532013000'
    # accounts of static/src/sample/camt053_sample.xml
    SAMPLE_IBAN = 'BE25734025189164'
    SAMPLE_CUSTOMER_IBAN = 'NL07RDGB0418302957'

    def customer_with_bank(self, iban=None):
        partner = self.env['res.partner'].create({'name': 'Kit Bank IBAN Customer'})
        self.env['res.partner.bank'].create({'account_number': iban or self.CUSTOMER_IBAN, 'partner_id': partner.id})
        return partner

    def camt(self, kind, blocks):
        """A CAMT file; ``blocks`` are (account, currency, [(ref, amount,
        day, name, label)])."""
        root, node, version = {
            '053': ('BkToCstmrStmt', 'Stmt', '053.001.02'),
            '054': ('BkToCstmrDbtCdtNtfctn', 'Ntfctn', '054.001.08'),
            '052': ('BkToCstmrAcctRpt', 'Rpt', '052.001.08'),
        }[kind]
        body = ''
        for number, (account, currency, entries) in enumerate(blocks, start=1):
            rows = ''.join(
                '<Ntry><Amt Ccy="%s">%.2f</Amt><CdtDbtInd>%s</CdtDbtInd><Sts><Cd>BOOK</Cd></Sts>'
                '<BookgDt><Dt>2026-04-%02d</Dt></BookgDt><AcctSvcrRef>%s</AcctSvcrRef><NtryDtls><TxDtls>'
                '<RltdPties><%s><Pty><Nm>%s</Nm></Pty></%s></RltdPties><RmtInf><Ustrd>%s</Ustrd></RmtInf>'
                '</TxDtls></NtryDtls></Ntry>' % (
                    currency, abs(amount), 'CRDT' if amount > 0 else 'DBIT', day, ref,
                    'Dbtr' if amount > 0 else 'Cdtr', name, 'Dbtr' if amount > 0 else 'Cdtr', label)
                for ref, amount, day, name, label in entries)
            body += '<%s><Id>N%s</Id><Acct><Id><IBAN>%s</IBAN></Id><Ccy>%s</Ccy></Acct>%s</%s>' % (
                node, number, account, currency, rows, node)
        return ('<?xml version="1.0"?><Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.%s">'
                '<%s><GrpHdr><MsgId>M</MsgId></GrpHdr>%s</%s></Document>' % (version, root, body, root))

    def test_camt053_sample(self):
        """CAMT.053: journal found from the IBAN, balances from OPBD /
        CLBD, a batch booking split per transaction, partner found by its
        IBAN, raw bank data and the file kept; re-import refused; a journal
        of another account or currency refuses the file."""
        journal = self.bank_journal(account='BE25 7340 2518 9164')
        customer = self.customer_with_bank(self.SAMPLE_CUSTOMER_IBAN)
        self.run_import(False, 'camt053_sample.xml', self.sample('camt053_sample.xml'))
        statement = self.statements(journal)
        self.assertEqual(len(statement), 1)
        self.assertEqual(sorted(statement.line_ids.mapped('amount')), [-199.9, -112.5, 860.25])
        self.assertAmount(statement.balance_start, 2400)
        self.assertAmount(statement.balance_end_real, 2947.85)
        self.assertTrue(statement.is_complete)
        deposit = statement.line_ids.filtered(lambda l: l.amount == 860.25)
        self.assertEqual(deposit.partner_id, customer)
        self.assertEqual(deposit.account_number, self.SAMPLE_CUSTOMER_IBAN)
        self.assertEqual(deposit.payment_ref, 'Payment INV/2026/00042')
        self.assertEqual(deposit.transaction_details['entry_reference'], 'KIT-E1')
        self.assertEqual(statement.attachment_ids.name, 'camt053_sample.xml')
        self.assertEqual(statement.attachment_ids.raw.content, self.sample('camt053_sample.xml'))
        self.assertIn('already imported', self.import_error(journal, 'camt053_sample.xml',
                                                            self.sample('camt053_sample.xml')))
        other = self.bank_journal(account='NL91ABNA0417164300')
        error = self.import_error(other, 'camt053_sample.xml', self.sample('camt053_sample.xml'))
        self.assertIn(self.SAMPLE_IBAN, error)
        self.assertIn('NL91 ABNA 0417 1643 00', error)
        foreign = 'EUR' if self.company.currency_id.name != 'EUR' else 'USD'
        error = self.import_error(self.bank_journal(), 'f.xml', self.camt('053', [(self.IBAN, foreign, [('X1', 5, 1, 'A', 'B')])]))
        self.assertIn(foreign, error)
        error = self.import_error(False, 'none.xml', self.camt('053', [('NL02ABNA0123456789', self.company.currency_id.name,
                                                                         [('X2', 5, 1, 'A', 'B')])]))
        self.assertIn('NL02ABNA0123456789', error)

    def test_camt054_several_notifications(self):
        """CAMT.054 with two notifications: two statements; CAMT.052
        report read the same way."""
        journal = self.bank_journal(account=self.IBAN)
        currency = self.company.currency_id.name
        self.run_import(journal, 'notif.xml', self.camt('054', [
            (self.IBAN, currency, [('N1', 40, 2, 'Client One', 'Order 1')]),
            (self.IBAN, currency, [('N2', -15, 3, 'Shop', 'Paper'), ('N3', 60, 3, 'Client Two', 'Order 2')]),
        ]))
        statements = self.statements(journal)
        self.assertEqual(len(statements), 2)
        self.assertEqual(statements.mapped('name'), ['notif - N1', 'notif - N2'])
        self.assertEqual(sorted(statements[1].line_ids.mapped('amount')), [-15, 60])
        self.assertEqual(statements[0].line_ids.partner_name, 'Client One')
        self.run_import(journal, 'report.xml', self.camt('052', [(self.IBAN, currency, [('R1', 7, 4, 'X', 'Intraday')])]))
        self.assertEqual(self.statements(journal)[-1:].line_ids.payment_ref, 'Intraday')

    def test_mt940(self):
        """MT940: Dutch (/NAME/ /REMI/) and German (?20 ?32 SVWZ+) details,
        balances, bank references against duplicates, several statements
        in one file, journal found from 'bank code/account' against its
        IBAN."""
        journal = self.bank_journal(account=self.IBAN)
        self.run_import(journal, 'mt940_sample.sta', self.sample('mt940_sample.sta'))
        statement = self.statements(journal)
        self.assertEqual(sorted(statement.line_ids.mapped('amount')), [-174.5, 500])
        self.assertAmount(statement.balance_start, 1000)
        self.assertAmount(statement.balance_end_real, 1325.5)
        dutch = statement.line_ids.filtered(lambda l: l.amount == 500)
        self.assertEqual((dutch.partner_name, dutch.payment_ref, dutch.ref),
                         ('Sample Customer', 'Invoice INV/2026/00001', 'E2E-1001'))
        german = statement.line_ids.filtered(lambda l: l.amount < 0)
        self.assertEqual((german.partner_name, german.payment_ref), ('Landlord Ltd', 'Rent March'))
        self.assertIn('already imported', self.import_error(journal, 'again.sta', self.sample('mt940_sample.sta')))
        german_journal = self.bank_journal(account='DE89 3704 0044 0532 0130 00')
        two = ("{1:F01BANKDEFFXXXX0000000000}{2:O940}{4:\n"
               ":20:ST1\n:25:37040044/0532013000\n:28C:1/1\n:60F:C260401EUR100,00\n"
               ":61:2604020402C25,00NTRFNONREF//B1\n:86:Customer pays\nOrder 9\n:62F:C260402EUR125,00\n-}\n"
               "{1:F01BANKDEFFXXXX0000000000}{2:O940}{4:\n"
               ":20:ST2\n:25:37040044/0532013000\n:28C:2/1\n:60F:C260402EUR125,00\n"
               ":61:260403D5,00NCHGNONREF//B2\n:86:Fees\n:62F:C260403EUR120,00\n-}\n")
        currency = self.company.currency_id.name
        self.run_import(False, 'two.sta', two.replace('EUR', currency))
        statements = self.statements(german_journal)
        self.assertEqual(len(statements), 2)
        self.assertEqual(statements[0].line_ids.payment_ref, 'Customer pays Order 9')
        self.assertAmount(statements[1].balance_end_real, 120)
        self.assertEqual(statements[1].line_ids.amount, -5)

    def test_saved_format(self):
        """A European CSV through the journal's saved format: lines above
        the header, semicolons, decimal comma, day.month.year dates,
        reversed sign, the bank's transaction ID against duplicates."""
        journal = self.bank_journal()
        self.env['kit.statement.import.map'].create({
            'name': 'Sparkasse', 'journal_id': journal.id, 'delimiter': 'semicolon', 'decimal_separator': 'comma',
            'date_format': 'dmy_dot', 'skip_rows': 2, 'reverse_sign': True, 'encoding': 'cp1252',
            'date_column': 'Buchungstag', 'amount_column': 'Betrag', 'label_column': 'Verwendungszweck',
            'partner_column': 'Empfänger', 'unique_id_column': 'Umsatz-ID'})
        csv = ("Konto;DE123\nZeitraum;April\n"
               "Buchungstag;Verwendungszweck;Empfänger;Betrag;Umsatz-ID\n"
               "01.04.2026;Miete April;Vermieter GmbH;1.234,56;U1\n"
               "02.04.2026;Gutschrift;Kunde;-50,00;U2\n").encode('cp1252')
        self.run_import(journal, 'umsatz.csv', csv)
        statement = self.statements(journal)
        self.assertEqual(sorted(statement.line_ids.mapped('amount')), [-1234.56, 50])
        self.assertEqual(statement.line_ids.filtered(lambda l: l.amount > 0).partner_name, 'Kunde')
        self.assertEqual(sorted(statement.line_ids.mapped('kit_import_id')),
                         ['%s|id|U1' % journal.id, '%s|id|U2' % journal.id])
        action = self.run_import(journal, 'umsatz2.csv', csv.replace(b'U2\n', b'U2\n03.04.2026;Neu;X;10,00;U3\n'))
        self.assertIn('2 already there', action['params']['message'])
        error = self.import_error(journal, 'wrong.csv', "Konto\nApril\nDatum;Betrag\n01.04.2026;5,00\n")
        self.assertIn('Buchungstag', error)

    def test_set_columns_and_save(self):
        """Unknown columns: the wizard lists them, the user says what each
        holds, the file imports and the format is saved for the journal;
        the next file of that bank imports at once."""
        journal = self.bank_journal()
        csv = "Booked;Text;In;Out\n2026-04-05;Salary;2500,00;\n2026-04-06;Shop;;19,90\n"
        wizard = self.env['import.bank.statement'].create({
            'attachment': base64.b64encode(csv.encode()).decode(), 'file_name': 'bank.csv', 'journal_id': journal.id})
        action = wizard.action_statement_import()
        self.assertEqual((action['res_model'], action['res_id']), ('import.bank.statement', wizard.id))
        self.assertEqual(wizard.state, 'columns')
        self.assertEqual(wizard.column_ids.mapped('name'), ['Booked', 'Text', 'In', 'Out'])
        self.assertIn('Salary', wizard.column_ids[1].sample)
        holds = {'Booked': 'date', 'Text': 'label', 'In': 'credit', 'Out': 'debit'}
        for line in wizard.column_ids:
            line.field = holds[line.name]
        wizard.column_ids[2].field = 'date'
        with self.assertRaises(UserError):
            wizard.action_statement_import()
        wizard.column_ids[2].field = 'credit'
        wizard.decimal_separator = 'comma'
        wizard.action_statement_import()
        self.assertEqual(sorted(self.statements(journal).line_ids.mapped('amount')), [-19.9, 2500])
        fmt = self.env['kit.statement.import.map'].search([('journal_id', '=', journal.id)])
        self.assertEqual((fmt.date_column, fmt.credit_column, fmt.debit_column, fmt.decimal_separator),
                         ('Booked', 'In', 'Out', 'comma'))
        self.assertEqual(journal.kit_import_map_ids, fmt)
        self.run_import(journal, 'bank2.csv', "Booked;Text;In;Out\n2026-04-07;Refund;12,30;\n")
        self.assertEqual(self.statements(journal)[-1:].line_ids.amount, 12.3)

    def test_several_files_and_email(self):
        """Several files at once: one statement each and a summary; the
        core hook for statements sent to the journal's email alias."""
        journal = self.bank_journal(account=self.IBAN)
        wizard = self.env['import.bank.statement'].create({
            'journal_id': journal.id,
            'attachment_ids': [(6, 0, self.attachments([
                ('a.csv', "date,label,amount\n2026-04-01,A,10\n"),
                ('b.sta', self.sample('mt940_sample.sta')),
            ]).ids)]})
        action = wizard.action_statement_import()
        self.assertIn('a.csv: 1 imported, 0 already there.', action['params']['message'])
        self.assertIn('b.sta: 2 imported, 0 already there.', action['params']['message'])
        self.assertEqual(len(self.statements(journal)), 2)
        self.assertEqual(action['params']['next']['domain'], [('id', 'in', self.statements(journal).ids)])
        mail_journal = self.bank_journal(account=self.SAMPLE_IBAN)
        result = mail_journal._import_bank_statement(self.attachments([
            ('mail.xml', self.sample('camt053_sample.xml').replace(b'KIT-E', b'KIT-MAIL-E'))]))
        lines = self.env['account.bank.statement.line'].search(result['domain'])
        self.assertEqual(len(lines), 3)
        self.assertIn(('kit_file_import', 'File Import'), mail_journal._get_bank_statements_available_sources())

    def test_amount_reading(self):
        """Amounts without a format: thousands and decimal signs guessed,
        trailing minus, currency codes."""
        wizard = self.env['import.bank.statement']
        for text, amount in (('1,234.56', 1234.56), ('1.234,56', 1234.56), ('12,5', 12.5), ('1,234', 1234),
                             ('100.00-', -100), ('(7.10)', -7.1), ('EUR 3 000,00', 3000), ("1'000.25", 1000.25)):
            self.assertAlmostEqual(wizard._parse_float(text), amount, msg=text)
        self.assertAlmostEqual(wizard._parse_float('1.234', decimal=','), 1234)
