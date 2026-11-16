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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProfitLossReport(models.TransientModel):
    """Wizard class for printing report."""

    _name = "profit.loss.report"
    _description = "profit and loss PDF report"

    start_date = fields.Date(string="Start date",
                             help="From which date do you want to generate"
                                  "report")
    end_date = fields.Date(string="End date",
                           help="To which date do you want to generate the"
                                "report")

    @api.constrains("start_date", "end_date")
    def check_start_date(self):
        """This function is used to validate the entered date"""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError(
                    self.env._("Please check the date that you provide"))

    def _get_account_lines(self, account_type, balance_type="income"):
        """Fetch account-wise totals for a given account_type.

        :param account_type: Account type to query (e.g. 'income', 'expense')
        :param balance_type: 'income' for (credit - debit), 'expense' for (debit - credit)
        """
        company = self.env.company
        root_company_id = str(company.root_id.id)
        active_company_id = str(company.id)
        lang = self.env.lang or "en_US"

        params = {
            "root_company_id": root_company_id,
            "active_company_id": active_company_id,
            "lang": lang,
            "account_type": account_type,
            "company_id": company.id,
        }

        code_expr = (
            "COALESCE(account_account.code_store ->> %(root_company_id)s, "
            "account_account.code_store ->> %(active_company_id)s, '')"
        )
        name_expr = (
            "COALESCE(account_account.name ->> %(lang)s, "
            "account_account.name ->> 'en_US', '')"
        )
        account_name_expr = (
            f"CASE WHEN {code_expr} != '' "
            f"THEN CONCAT({code_expr}, ' - ', {name_expr}) "
            f"ELSE {name_expr} END"
        )

        if balance_type == "income":
            balance_sql = "COALESCE(account_move_line.credit, 0.0) - COALESCE(account_move_line.debit, 0.0)"
        else:
            balance_sql = "COALESCE(account_move_line.debit, 0.0) - COALESCE(account_move_line.credit, 0.0)"

        where_clause = (
            "account_account.account_type = %(account_type)s "
            "AND account_move_line.company_id = %(company_id)s "
            "AND account_move_line.parent_state = 'posted'"
        )
        if self.start_date:
            where_clause += " AND account_move_line.date >= %(start_date)s"
            params["start_date"] = self.start_date
        if self.end_date:
            where_clause += " AND account_move_line.date <= %(end_date)s"
            params["end_date"] = self.end_date

        query = f"""
            SELECT {code_expr} AS code,
                   {name_expr} AS name,
                   {account_name_expr} AS account_name,
                   account_account.account_type,
                   SUM({balance_sql}) AS balance
            FROM account_move_line
            JOIN account_account ON account_account.id = account_move_line.account_id
            WHERE {where_clause}
            GROUP BY {code_expr}, {name_expr}, account_account.account_type
        """

        self.env.cr.execute(query, params)
        lines = self.env.cr.dictfetchall()

        total = 0.0
        for item in lines:
            val = round(float(item["balance"] or 0.0), 2)
            item["balance"] = val
            item["sum"] = val
            item["debit"] = val
            item["credit"] = val
            total += val

        return lines, round(total, 2)

    def action_button_to_print_pdf(self):
        """Print pdf report of profit and loss report"""
        self.env.flush_all()
        op_income, total_op_income = self._get_account_lines(
            "income", balance_type="income",
        )
        other_income, total_other_income = self._get_account_lines(
            "income_other", balance_type="income",
        )
        cor, total_cor = self._get_account_lines(
            "expense_direct_cost", balance_type="expense",
        )
        exp, net_exp = self._get_account_lines(
            "expense", balance_type="expense",
        )
        dep, net_dep = self._get_account_lines(
            "expense_depreciation", balance_type="expense",
        )
        other_exp, total_other_exp = self._get_account_lines(
            "expense_other", balance_type="expense",
        )

        total_income = round(total_op_income + total_other_income, 2)
        gross_profit = round(total_op_income - total_cor, 2)
        total_expense = round(net_exp + net_dep + total_other_exp, 2)
        net_profit = round(gross_profit + total_other_income - total_expense, 2)

        data = {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "net_profit": net_profit,
            "income": total_income,
            "gross_profit": gross_profit,
            "operating_income": op_income,
            "total_op_income": total_op_income,
            "cost_of_revenue": cor,
            "total_cor": total_cor,
            "other_income": other_income,
            "total_other_income": total_other_income,
            "net_expense": total_expense,
            "expense": exp,
            "total_expense": net_exp,
            "depreciation": dep,
            "total_depreciation": net_dep,
            "other_expense": other_exp,
            "total_other_expense": total_other_exp,
            "company_id": self.env.company.id,
            "res_company": self.env.company,
            "today": fields.Datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        return self.env.ref(
            "profit_and_loss_pdf_report.pl_report_pdf").report_action(
            self, data=data, config=False)
