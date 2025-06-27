from odoo import api, fields, models


class HrPayslip(models.Model):
    """ This class extends hr.payslip to include bonus amounts in payslip calculation. """
    _inherit = "hr.payslip"

    @api.onchange('employee_id', 'date_from', 'date_to', 'struct_id')
    def _onchange_employee(self):
        """ When changing employee, load bonus amount as other input """
        self.ensure_one()  # Ensure single record for onchange
        bonus_rule = self.env.ref('employee_bonus_manager.hr_salary_rule_bonus')
        rules = self.struct_id.rule_ids.mapped('name')
        if bonus_rule.name in rules:
            bonus = self.env['bonus.request'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'posted'),
                ('move_id.state', '=', 'posted'),
                ('move_id.date', '>=', self.date_from),
                ('move_id.date', '<=', self.date_to)
            ])
            amount = sum(bonus.mapped('bonus_amount'))
            self.input_line_ids = [(0, 0, {
                'name': 'Bonus',
                'code': 'BONUS',
                'contract_id': self.contract_id.id,
                'amount': amount,
            })]
