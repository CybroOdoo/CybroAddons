from odoo import api, fields, models, _


class HRSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_lunch = fields.Boolean(string='Is Lunch ?')


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def compute_sheet(self):
        """overrding the compute sheet method to add the lunch value to the payslip"""
        for payslip in self:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                           self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            lunch_rules = self.env['hr.salary.rule'].search([('is_lunch', '=', True)]).mapped('id')
            for line in lines:
                if line[2]['salary_rule_id'] in lunch_rules:
                    amount = self.compute_lunch()
                    line[2]['amount'] = -amount
            payslip.write({'line_ids': lines, 'number': number})
        return True

    @api.multi
    def compute_lunch(self):
        employee = self.employee_id
        amount = 0
        user_id = employee.user_id
        if user_id:
            lunch_rec = self.env['lunch.order'].search([('user_id', '=', user_id.id),
                                                        ('date', '>=', self.date_from),
                                                        ('date', '<=', self.date_to),
                                                        ('state', '=', 'confirmed')])
            if lunch_rec:
                amount = sum(lunch_rec.mapped('total'))
        return amount
