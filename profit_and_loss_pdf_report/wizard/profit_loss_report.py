# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProfitLossReport(models.TransientModel):
    """Wizard class for printing report."""

    _name = "profit.loss.report"
    _description = "profit and loss PDF report"

    start_date = fields.Date(
        string="Start date", help="From which date do you want to generate the" "report"
    )
    end_date = fields.Date(
        string="End date", help="To which date do you want to generate the" "report"
    )

    @api.constrains("start_date", "end_date")
    def check_start_date(self):
        """This function is used to validate the entered date"""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError(_("Please check the date that you " "provide"))

    def action_button_to_print_pdf(self):
        """Print pdf report of profit and loss report"""
        query = f"""
        select account_account.code,account_account.name,
        CONCAT(account_account.code, ' - ',account_account.name) 
        AS account_name,account_account.internal_group,
        sum(account_move_line.credit) 
        from account_move_line join account_account on account_account.id = 
         account_move_line.account_id 
        where internal_group='income' 
        AND account_move_line.company_id = '{self.env.company.id}'
        """
        if self.start_date:
            query += f""" AND account_move_line.date >= '{self.start_date}' """
        if self.end_date:
            query += f""" AND account_move_line.date <= '{self.end_date}' """
        query += (
            " group by account_account.code,account_account.name,"
            "account_account.internal_group"
        )
        self.env.cr.execute(query, [self.start_date, self.end_date])
        op_income = self.env.cr.dictfetchall()
        total_op_income = 0.0
        op_income_lst = []
        for op_inc in op_income:
            net = op_inc["sum"]
            op_income_lst.append(net)
            total_op_income = sum(op_income_lst)
        query_other_income = f"""
        select account_account.code,account_account.name,
        CONCAT(account_account.code, ' - ', account_account.name) AS 
        account_name,account_account.internal_group,sum(account_move_line.credit) 
        from account_move_line join account_account on
        account_account.id = account_move_line.account_id
        where internal_group='income_other' 
        AND account_move_line.company_id = '{self.env.company.id}'
       """
        if self.start_date:
            query_other_income += f""" AND account_move_line.date >=
                '{self.start_date}' """
        if self.end_date:
            query_other_income += f"""AND account_move_line.date <=
            '{self.end_date}' """
        query_other_income += (
            " group by account_account.code"
            ",account_account.name,account_account.internal_group"
        )
        self.env.cr.execute(query_other_income)
        other_income = self.env.cr.dictfetchall()
        total_other_income = 0.0
        other_income_lst = []
        for o_income in other_income:
            net = o_income["sum"]
            other_income_lst.append(net)
            total_other_income = sum(other_income_lst)
        query_cor = f"""
        select account_account.code,account_account.name,
        CONCAT(account_account.code, ' - ',account_account.name) 
        AS account_name,account_account.internal_group,
        sum(account_move_line.credit)
        from account_move_line join account_account on account_account.id =
        account_move_line.account_id
        where internal_group='expense_direct_cost' AND 
        account_move_line.company_id = '{self.env.company.id}'
        """
        if self.start_date:
            query_cor += f""" AND account_move_line.date >= '{self.start_date}'
            """
        if self.end_date:
            query_cor += f""" AND account_move_line.date <= '{self.end_date}'
                        """
        query_cor += (
            " group by account_account.code,account_account.name,"
            "account_account.internal_group"
        )
        self.env.cr.execute(query_cor)
        cor = self.env.cr.dictfetchall()
        total_cor = 0.0
        cor_lst = []
        for revenue in cor:
            net = revenue["sum"]
            cor_lst.append(net)
            total_cor = sum(cor_lst)
        query_expense = f"""
        select account_account.code,account_account.name, 
        CONCAT(account_account.code, ' - ', account_account.name) AS
        account_name,account_account.internal_group,sum(account_move_line.debit)
        debit from account_move_line join account_account on account_account.id
         = account_move_line.account_id where internal_group='expense' 
         AND  account_move_line.company_id = '{self.env.company.id}'
        """
        if self.start_date:
            query_expense += f""" AND account_move_line.date >=
             '{self.start_date}' """
        if self.end_date:
            query_expense += f""" AND account_move_line.date <=
            '{self.end_date}'"""
        query_expense += (
            " group by account_account.code,account_account.name,"
            "account_account.internal_group"
        )
        self.env.cr.execute(query_expense)
        exp = self.env.cr.dictfetchall()
        net_exp = 0.0
        total_exp = []
        for expense in exp:
            net = expense["debit"]
            total_exp.append(net)
            net_exp = sum(total_exp)
        query_depreciation = f"""
               select account_account.code,account_account.name,
               CONCAT(account_account.code, ' - ', account_account.name) 
               AS account_name, account_account.internal_group,
               sum(account_move_line.credit) credit from account_move_line
               join account_account on account_account.id = 
               account_move_line.account_id where internal_group
               ='expense_depreciation'
               AND  account_move_line.company_id = '{self.env.company.id}'
               """
        if self.start_date:
            query_depreciation += f""" AND account_move_line.date >=
             '{self.start_date}' """
        if self.end_date:
            query_depreciation += f""" AND account_move_line.date <=
             '{self.end_date}' """
        query_depreciation += (
            " group by account_account.code,"
            "account_account.name,account_account.internal_group"
        )
        self.env.cr.execute(query_depreciation)
        dep = self.env.cr.dictfetchall()
        net_dep = 0.0
        total_dep = []
        for depreciation in dep:
            net = depreciation["credit"]
            total_dep.append(net)
            net_dep = sum(total_dep)
        net_profit = (
            (total_op_income + total_other_income) - total_cor - net_exp - net_dep
        )
        total_expense = net_exp + net_dep
        data = {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "net_profit": net_profit,
            "income": total_op_income + total_other_income,
            "gross_profit": total_op_income - total_cor,
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
        }
        return self.env.ref("profit_and_loss_pdf_report.pl_report_pdf").report_action(
            self, data=data
        )
