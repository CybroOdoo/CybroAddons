# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class HrPayslip(models.Model):
    """Extend the hr.payslip model to include additional functionality."""
    _inherit = 'hr.payslip'

    leave_salary = fields.Boolean(string='Leave Salary',
                                  help="Check leave if salary should be paid"
                                       " for the employee if is on ,leave")

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        """Retrieve and compute the salary rule lines for the given
        contracts and payslip."""

        def _sum_salary_rule_category(localdict, category, wage):
            """Recursively calculates the total amount for a specific salary
             rule category and its parent categories.
             Args:
            localdict (dict): A dictionary containing the local variables,
            including the 'categories' sub-dictionary.
            category (SalaryRuleCategory): The salary rule category for which
            the amount is calculated.
            amount (float): The amount to be added to the category."""
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict,
                                                      category.parent_id,
                                                      wage)
            localdict['categories'].dict[category.code] = \
                (category.code in localdict['categories'].dict and
                 localdict['categories'].dict[category.code] + wage or wage
                 )
            return localdict

        class BrowsableObject(object):
            """Represents a browsable object with attributes accessible
            through the __getattr__ method."""

            def __init__(self, employee_id, dict, env):
                """Initializes a BrowsableObject with the provided parameters.
                Parameters:
                employee_id (str): The unique identifier for the employee.
                dict (dict): A dictionary containing attribute-value pairs for
                the object.
                env: The environment associated with the object."""
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                """Retrieve the value of the specified attribute from the
                internal dictionary.
                If the attribute is present in the dictionary, return its
                value. If the attribute is not found, return 0.0."""
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """A class that will be used into the python code, mainly for
            usability purposes"""

            def sum(self, code, from_date, to_date=None):
                """Calculate the sum of amounts for a specified payroll
                code within a date range."""
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND 
                    hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id,
                                     from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """A class that will be used into the python code, mainly for
            usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days,
                     sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND 
                    hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date,
                                     code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                """Calculate the sum of amounts for a specified payroll
                code within a date range."""
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """A class that will be used into the python code, mainly
            for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                """Calculate the sum of amounts for a specified payroll code
                 within a date range.
                We keep a dict with the result because a value can be
                overwritten by another rule with the same code"""
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = 
                False then (pl.total) else (-pl.total) end)
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND 
                            hp.id = pl.slip_id AND pl.code = %s""",
                                    (self.employee_id, from_date, to_date,
                                     code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line
        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict,
                                 self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)
        baselocaldict = {'categories': categories, 'rules': rules,
                         'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs}
        contracts = self.env['hr.version'].browse(contract_ids)
        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        if payslip.leave_salary:
            leave_sal_basic = self.env.ref(
                'hr_vacation_mngmt.hr_salary_rule_leave_salary_basic')
            leave_sal_gross = self.env.ref(
                'hr_vacation_mngmt.hr_salary_rule_leave_salary_gross')
            default_leave_salary = self.env[
                'ir.config_parameter'].sudo().get_param('default_leave_salary')
            if default_leave_salary == '0':
                leave_salary = leave_sal_basic
            elif default_leave_salary == '1':
                leave_salary = leave_sal_gross
            else:
                leave_salary = leave_sal_basic
            rule_ids.append((leave_salary.id, leave_salary.sequence))
        sorted_rule_ids = [id for id, sequence in
                           sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)
        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                if rule._satisfy_condition(
                        localdict) and rule.id not in blacklist:
                    amount, qty, rate = rule._compute_rule(localdict)
                    previous_amount = rule.code in localdict and localdict[
                        rule.code] or 0.0
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    localdict = _sum_salary_rule_category(localdict,
                                                          rule.category_id,
                                                          tot_rule - previous_amount)
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    blacklist += [id for id, seq in
                                  rule._recursive_search_of_rules()]
        return list(result_dict.values())
