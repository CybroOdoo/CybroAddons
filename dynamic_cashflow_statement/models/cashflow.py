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
from odoo import fields, models


class Cashflow(models.Model):
    """Read a cash flow report from posted liquidity account move lines."""

    _name = "cashflow"
    _description = "Cash flow report"

    def get_report_values(self, data=None):
        """Return cash receipts and payments for the selected period."""
        self.check_access("read")
        data = data or {}
        allowed_company_ids = self.env.companies.ids
        requested_company_ids = data.get("company_ids")
        if requested_company_ids is not None:
            requested_company_ids = set(requested_company_ids)
            allowed_company_ids = [
                company_id for company_id in allowed_company_ids
                if company_id in requested_company_ids
            ]

        domain = [
            ("move_id.state", "=", "posted"),
            ("company_id", "in", allowed_company_ids),
            ("account_id.account_type", "=", "asset_cash"),
        ]
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        if date_from:
            fields.Date.to_date(date_from)
            domain.append(("date", ">=", date_from))
        if date_to:
            fields.Date.to_date(date_to)
            domain.append(("date", "<=", date_to))

        lines = self.env["account.move.line"].search_read(
            domain,
            ["account_id", "journal_id", "move_id", "name", "debit", "credit"],
            order="account_id, journal_id, date, id",
        )
        account_ids = {line["account_id"][0] for line in lines}
        account_codes = {
            account["id"]: account["code"]
            for account in self.env["account.account"].browse(account_ids).read(["code"])
        }
        grouped_accounts = {}
        for line in lines:
            account_id, account_name = line["account_id"]
            journal_id, journal_name = line["journal_id"]
            move_id, move_name = line["move_id"]
            account = grouped_accounts.setdefault(account_id, {
                "account": account_name,
                "code": account_codes[account_id],
                "total_debit": 0.0,
                "total_credit": 0.0,
                "move_lines": [],
                "journal_lines": {},
            })
            debit = line["debit"]
            credit = line["credit"]
            account["total_debit"] += debit
            account["total_credit"] += credit
            account["move_lines"].append({
                "id": line["id"],
                "move_id": move_id,
                "account_id": account_id,
                "move_name": move_name,
                "name": journal_name,
                "line_name": line["name"],
                "total_debit": debit,
                "total_credit": credit,
            })
            journal = account["journal_lines"].setdefault(journal_id, {
                "id": journal_id,
                "name": journal_name,
                "total_debit": 0.0,
                "total_credit": 0.0,
            })
            journal["total_debit"] += debit
            journal["total_credit"] += credit

        account_res = []
        for account in grouped_accounts.values():
            account["journal_lines"] = list(account["journal_lines"].values())
            account_res.append(account)
        return {
            "fetched_data": account_res,
            "journal_res": [],
            "account_res": account_res,
        }
