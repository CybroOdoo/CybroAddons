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
from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProfitLossReport(TransactionCase):
    """Test suite for Profit and Loss PDF Report module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.today = fields.Date.today()
        cls.test_date = fields.Date.to_date("2035-05-15")
        cls.test_start = fields.Date.to_date("2035-05-01")
        cls.test_end = fields.Date.to_date("2035-05-31")

        # Find or create a general journal
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        if not cls.journal:
            cls.journal = cls.env["account.journal"].create({
                "name": "Test General Journal",
                "code": "TGJ",
                "type": "general",
                "company_id": cls.company.id,
            })

        # Create balancing cash / payable account
        cls.account_cash = cls.env["account.account"].create({
            "name": "Test Cash Account",
            "code": "TCASH01",
            "account_type": "asset_cash",
        })

        # Create test accounts for all P&L categories
        cls.account_income = cls.env["account.account"].create({
            "name": "Test Operating Income",
            "code": "TINC01",
            "account_type": "income",
        })
        cls.account_income_other = cls.env["account.account"].create({
            "name": "Test Other Income",
            "code": "TOINC01",
            "account_type": "income_other",
        })
        cls.account_cor = cls.env["account.account"].create({
            "name": "Test Cost of Revenue",
            "code": "TCOR01",
            "account_type": "expense_direct_cost",
        })
        cls.account_expense = cls.env["account.account"].create({
            "name": "Test Operating Expense",
            "code": "TEXP01",
            "account_type": "expense",
        })
        cls.account_depreciation = cls.env["account.account"].create({
            "name": "Test Depreciation Expense",
            "code": "TDEP01",
            "account_type": "expense_depreciation",
        })
        cls.account_expense_other = cls.env["account.account"].create({
            "name": "Test Other Expense",
            "code": "TOEXP01",
            "account_type": "expense_other",
        })

    def _create_move(self, lines, post=True, move_date=None):
        """Helper to create and optionally post an account.move."""
        move = self.env["account.move"].create({
            "journal_id": self.journal.id,
            "date": move_date or self.today,
            "line_ids": [Command.create(line) for line in lines],
        })
        if post:
            move.action_post()
        self.env.flush_all()
        return move

    def test_01_module_installed(self):
        """Verify module is registered."""
        module = self.env["ir.module.module"].search([
            ("name", "=", "profit_and_loss_pdf_report"),
        ])
        self.assertTrue(module, "Module profit_and_loss_pdf_report must be registered.")

    def test_02_wizard_date_validation(self):
        """Test wizard date constraint validation."""
        # Case 1: start_date > end_date raises ValidationError on create
        with self.assertRaises(ValidationError):
            self.env["profit.loss.report"].create({
                "start_date": fields.Date.to_date("2026-12-31"),
                "end_date": fields.Date.to_date("2026-01-01"),
            })

        # Case 2: valid dates succeed without error
        wizard_valid = self.env["profit.loss.report"].create({
            "start_date": fields.Date.to_date("2026-01-01"),
            "end_date": fields.Date.to_date("2026-12-31"),
        })
        wizard_valid.check_start_date()

        # Case 3: single date provided succeeds
        wizard_single = self.env["profit.loss.report"].create({
            "start_date": fields.Date.to_date("2026-01-01"),
            "end_date": False,
        })
        wizard_single.check_start_date()

    def test_03_default_wizard_execution(self):
        """Verify wizard execution with default empty date filters."""
        wizard = self.env["profit.loss.report"].create({})
        action = wizard.action_button_to_print_pdf()

        self.assertIsInstance(action, dict, "Wizard action must return a dictionary.")
        self.assertEqual(action.get("type"), "ir.actions.report")
        self.assertEqual(
            action.get("report_name"),
            "profit_and_loss_pdf_report.pl_report_temp",
        )
        self.assertIn("data", action)
        data = action["data"]
        self.assertIn("net_profit", data)
        self.assertIn("income", data)
        self.assertIn("gross_profit", data)
        self.assertIn("net_expense", data)

    def test_04_full_profit_loss_calculations(self):
        """Test P&L calculations with posted moves, returns, and excluded draft entries."""
        # 1. Operating Income: 10,000 credit
        self._create_move([
            {"account_id": self.account_income.id, "name": "Sale 1", "credit": 10000.0, "debit": 0.0},
            {"account_id": self.account_cash.id, "name": "Cash", "credit": 0.0, "debit": 10000.0},
        ], move_date=self.test_date)

        # 2. Operating Income Return (Customer Credit Note): 1,000 debit (netting test)
        self._create_move([
            {"account_id": self.account_income.id, "name": "Return", "credit": 0.0, "debit": 1000.0},
            {"account_id": self.account_cash.id, "name": "Cash Refund", "credit": 1000.0, "debit": 0.0},
        ], move_date=self.test_date)

        # 3. Other Income: 2,000 credit
        self._create_move([
            {"account_id": self.account_income_other.id, "name": "Interest", "credit": 2000.0, "debit": 0.0},
            {"account_id": self.account_cash.id, "name": "Cash", "credit": 0.0, "debit": 2000.0},
        ], move_date=self.test_date)

        # 4. Cost of Revenue: 3,000 debit
        self._create_move([
            {"account_id": self.account_cor.id, "name": "Raw materials", "credit": 0.0, "debit": 3000.0},
            {"account_id": self.account_cash.id, "name": "Cash", "credit": 3000.0, "debit": 0.0},
        ], move_date=self.test_date)

        # 5. Operating Expense: 1,000 debit
        self._create_move([
            {"account_id": self.account_expense.id, "name": "Office Supplies", "credit": 0.0, "debit": 1000.0},
            {"account_id": self.account_cash.id, "name": "Cash", "credit": 1000.0, "debit": 0.0},
        ], move_date=self.test_date)

        # 6. Expense Refund (Vendor Credit Note): 100 credit (netting test)
        self._create_move([
            {"account_id": self.account_expense.id, "name": "Supplies Rebate", "credit": 100.0, "debit": 0.0},
            {"account_id": self.account_cash.id, "name": "Cash", "credit": 0.0, "debit": 100.0},
        ], move_date=self.test_date)

        # 7. Depreciation: 500 debit
        self._create_move([
            {"account_id": self.account_depreciation.id, "name": "Machinery Depr", "credit": 0.0, "debit": 500.0},
            {"account_id": self.account_cash.id, "name": "Cash", "credit": 500.0, "debit": 0.0},
        ], move_date=self.test_date)

        # 8. Other Expense: 200 debit
        self._create_move([
            {"account_id": self.account_expense_other.id, "name": "Bank Charges", "credit": 0.0, "debit": 200.0},
            {"account_id": self.account_cash.id, "name": "Cash", "credit": 200.0, "debit": 0.0},
        ], move_date=self.test_date)

        # 9. Draft Entry: 50,000 income (MUST be excluded)
        self._create_move(
            [
                {"account_id": self.account_income.id, "name": "Draft Sale", "credit": 50000.0, "debit": 0.0},
                {"account_id": self.account_cash.id, "name": "Cash", "credit": 0.0, "debit": 50000.0},
            ],
            post=False,
            move_date=self.test_date,
        )

        wizard = self.env["profit.loss.report"].create({
            "start_date": self.test_start,
            "end_date": self.test_end,
        })
        action = wizard.action_button_to_print_pdf()
        data = action["data"]

        # Expected calculations:
        # Operating Income: 10,000 - 1,000 = 9,000
        self.assertEqual(data["total_op_income"], 9000.0)

        # Other Income: 2,000
        self.assertEqual(data["total_other_income"], 2000.0)

        # Total Income: 9,000 + 2,000 = 11,000
        self.assertEqual(data["income"], 11000.0)

        # Cost of Revenue: 3,000
        self.assertEqual(data["total_cor"], 3000.0)

        # Gross Profit: 9,000 - 3,000 = 6,000
        self.assertEqual(data["gross_profit"], 6000.0)

        # Operating Expense: 1,000 - 100 = 900
        self.assertEqual(data["total_expense"], 900.0)

        # Depreciation: 500
        self.assertEqual(data["total_depreciation"], 500.0)

        # Other Expense: 200
        self.assertEqual(data["total_other_expense"], 200.0)

        # Total Expense: 900 + 500 + 200 = 1,600
        self.assertEqual(data["net_expense"], 1600.0)

        # Net Profit: Gross Profit (6,000) + Other Income (2,000) - Total Expense (1,600) = 6,400
        self.assertEqual(data["net_profit"], 6400.0)

    def test_05_date_filtering(self):
        """Verify date filtering properly includes/excludes period moves."""
        filter_date = fields.Date.to_date("2034-03-15")
        self._create_move(
            [
                {"account_id": self.account_income.id, "name": "Period Sale", "credit": 5000.0, "debit": 0.0},
                {"account_id": self.account_cash.id, "name": "Cash", "credit": 0.0, "debit": 5000.0},
            ],
            move_date=filter_date,
        )

        # Query for a non-overlapping date range: entry should not appear
        outside_wizard = self.env["profit.loss.report"].create({
            "start_date": fields.Date.to_date("2034-06-01"),
            "end_date": fields.Date.to_date("2034-06-30"),
        })
        outside_action = outside_wizard.action_button_to_print_pdf()
        outside_data = outside_action["data"]

        self.assertEqual(outside_data["total_op_income"], 0.0)
        self.assertEqual(outside_data["net_profit"], 0.0)

        # Query covering filter date: entry should appear
        inside_wizard = self.env["profit.loss.report"].create({
            "start_date": fields.Date.to_date("2034-03-01"),
            "end_date": fields.Date.to_date("2034-03-31"),
        })
        inside_action = inside_wizard.action_button_to_print_pdf()
        inside_data = inside_action["data"]

        self.assertEqual(inside_data["total_op_income"], 5000.0)
        self.assertEqual(inside_data["net_profit"], 5000.0)

    def test_06_pdf_report_rendering(self):
        """Test that QWeb PDF report renders without template errors."""
        wizard = self.env["profit.loss.report"].create({
            "start_date": self.test_start,
            "end_date": self.test_end,
        })
        action = wizard.action_button_to_print_pdf()

        # Render QWeb PDF template (returns html format in test mode without wkhtmltopdf)
        pdf_content, doc_format = self.env["ir.actions.report"]._render_qweb_pdf(
            "profit_and_loss_pdf_report.pl_report_pdf",
            res_ids=wizard.ids,
            data=action.get("data"),
        )
        self.assertTrue(pdf_content, "Generated PDF content should not be empty.")
        self.assertIn(doc_format, ["pdf", "html"], "Report format should be pdf or html.")
