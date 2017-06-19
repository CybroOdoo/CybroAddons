# -*- coding: utf-8 -*-
from datetime import datetime
from openerp import models


class SalaryRuleInput(models.Model):
    _inherit = 'hr.payslip'

    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = super(SalaryRuleInput, self).get_inputs(cr, uid, contract_ids, date_from, date_to, context=None)
        contract_obj = self.pool.get('hr.contract')
        emp_id = contract_obj.browse(cr, uid, contract_ids[0], context=context).employee_id.name
        adv_salary = self.pool.get('salary.advance').search(cr, uid, [('employee_id', '=', emp_id)])
        for each_employee in adv_salary:
            current_date = datetime.strptime(date_from, '%Y-%m-%d').date().month
            date = self.pool.get('salary.advance').browse(cr, uid, each_employee, context).date
            existing_date = datetime.strptime(date, '%Y-%m-%d').date().month
            if current_date == existing_date:
                adv_browse = self.pool.get('salary.advance').browse(cr, uid, each_employee, context)
                state = adv_browse.state
                amount = adv_browse.advance
                for result in res:
                    if state == 'approved' and amount != 0 and result.get('code') == 'SAR':
                        result['amount'] = amount
        return res
