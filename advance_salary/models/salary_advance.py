# -*- coding: utf-8 -*-
from datetime import datetime
from openerp import models, fields, api, _
from openerp.osv import osv
from openerp.exceptions import Warning


def _employee_get(obj, cr, uid, context=None):
    if context is None:
        context = {}
    ids = obj.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)], context=context)
    if ids:
        return ids[0]
    return False


def _get_currency(self, cr, uid, context=None):
    user = self.pool.get('res.users').browse(cr, uid, [uid], context=context)[0]
    return user.company_id.currency_id.id


class SalaryAdvancePayment(models.Model):
    _name = "salary.advance"
    name = fields.Char(string='Name', readonly=True, select=True, default=lambda self: 'Adv/')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default='_employee_get')
    date = fields.Date(string='Date', required=True, default=lambda self: fields.Date.today())
    reason = fields.Text(string='Reason')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default='_get_currency')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    advance = fields.Float(string='Advance', required=True)
    payment_method = fields.Many2one('account.journal', string='Payment Method', required=True)
    exceed_condition = fields.Boolean(string='Exceed than maximum')
    department = fields.Many2one('hr.department', string='Department')
    state = fields.Selection([('draft', 'Draft'),
                              ('approved', 'Approved'),
                              ('cancel', 'Cancel')], string='Status')

    @api.onchange('currency_id')
    def onchange_currency_id(self, currency_id=False, company_id=False):
        res = {'value': {'journal_id': False}}
        journal_ids = self.pool.get('account.journal').search(self._cr, self._uid, [('type', '=', 'purchase'),
                                                                                    ('currency', '=', currency_id),
                                                                                    ('company_id', '=', company_id)])
        if journal_ids:
            res['value']['journal_id'] = journal_ids[0]
        return res

    @api.onchange('company_id')
    def onchange_company_id(self):
        company = self.company_id
        domain = [('company_id.id', '=', company.id), ]
        result = {
            'domain': {
                'payment_method': domain,
            },

        }
        return result

    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        emp_obj = self.pool.get('hr.employee')
        department_id = False
        if employee_id:
            employee = emp_obj.browse(cr, uid, employee_id, context=context)
            department_id = employee.department_id.id
        return {'value': {'department': department_id}}

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('adv')
        emp_id = vals.get('employee_id')
        contract_obj = self.env['hr.contract']
        emp_obj = self.env['hr.employee']
        search_contract = contract_obj.search([('employee_id', '=', emp_id)])
        address = emp_obj.browse([emp_id]).address_home_id
        if not address.id:
            raise osv.except_osv('Error!', 'Define home address for employee')
        salary_advance_search = self.search([('employee_id', '=', emp_id)])
        for each_advance in salary_advance_search:
            current_month = datetime.strptime(vals.get('date'), '%Y-%m-%d').date().month
            existing_month = datetime.strptime(each_advance.date, '%Y-%m-%d').date().month
            if current_month == existing_month or current_month < existing_month:
                raise osv.except_osv('Error!', 'Advance can be requested once in a month')
        if not search_contract:
            raise osv.except_osv('Error!', 'Define a contract for the employee')
        for each_contract in search_contract:
            struct_id = each_contract.struct_id
            if not struct_id.max_percent or not struct_id.advance_date:
                raise osv.except_osv('Error!', 'Max percentage or advance days are not provided')
            adv = vals.get('advance')
            amt = (each_contract.struct_id.max_percent * each_contract.wage) / 100
            if adv > each_contract.wage:
                raise osv.except_osv('Error!', 'Advance amount is greater than Wage')
            if adv > amt and vals.get('exceed_condition') == False:
                raise osv.except_osv('Error!', 'Advance amount is greater than allotted')
        vals.update({'state': 'draft'})
        res_id = super(SalaryAdvancePayment, self).create(vals)
        return res_id

    @api.multi
    def write(self, vals):
        emp_id = self.employee_id.id
        date = self.date
        advance = self.advance
        if 'employee_id' in vals:
            emp_id = vals.get('employee_id')
        if 'date' in vals:
            date = vals.get('date')
        if 'advance' in vals:
            advance = vals.get('advance')
        contract = self.env['hr.contract']
        search_contract = contract.search([('employee_id', '=', emp_id)])
        emp_obj = self.env['hr.employee']
        address = emp_obj.browse([emp_id]).address_home_id
        if not address.id:
            raise osv.except_osv('Error!', 'Define home address for employee')
        salary_advance_search = self.search([('employee_id', '=', emp_id)])
        for each_advance in salary_advance_search:
            current_month = datetime.strptime(date, '%Y-%m-%d').date().month
            existing_month = datetime.strptime(each_advance.date, '%Y-%m-%d').date().month
            if each_advance.id != self.id and (current_month == existing_month or current_month < existing_month):
                raise osv.except_osv('Error!', 'Advance can be requested once in a month')
        if not search_contract:
            raise osv.except_osv('Error!', 'Define a contract for the employee')
        for each_contract in search_contract:
            if not each_contract.struct_id.max_percent or not each_contract.struct_id.advance_date:
                raise osv.except_osv('Error!', 'Max percentage or advance days are not provided')
            amt = (each_contract.struct_id.max_percent * each_contract.wage) / 100
            if advance > each_contract.wage:
                raise osv.except_osv('Error!', 'Advance amount is greater than Wage')
            if advance > amt and vals.get('exceed_condition') == False:
                raise osv.except_osv('Error!', 'Advance amount is greater than allotted')
        super(SalaryAdvancePayment, self).write(vals)
        return True

    def compute_advance_totals(self, account_move_lines):
        total = 0.0
        for i in account_move_lines:
            total -= i['price']
        return total, account_move_lines

    def line_get_convert(self, x, part, date):
        partner_id = self.env['res.partner']._find_accounting_partner(part).id
        res = {
            'date_maturity': x.get('date_maturity', False),
            'partner_id': partner_id,
            'name': x.get('name'),
            'date': date,
            'debit': x['price'] > 0 and x['price'],
            'credit': x['price'] < 0 and -x['price'],
            'account_id': x['account_id'],
            'analytic_lines': x.get('analytic_lines', False),
            'amount_currency': x['price'] > 0 and abs(x.get('amount_currency', False)) or -abs(
                x.get('amount_currency', False)),
            'currency_id': x.get('currency_id', False),
            'ref': x.get('ref', False),
            'product_id': x.get('product_id', False),
            'product_uom_id': x.get('uos_id', False),
            'analytic_account_id': x.get('account_analytic_id', False),
        }
        return res

    def account_adv_get(self, salary_adv_obj):
        return self.env['account.move'].account_move_prepare(salary_adv_obj.journal.id, date=False,
                                                             ref=self.employee_id.name, company_id=False)

    @api.one
    def approve(self):
        self.employee_id.write({'advance_amount': self.advance})
        move_obj = self.env['account.move']
        company_id = self.env['res.users'].browse(self._uid).company_id
        salary_adv_obj = self.env['advance.rules'].search([('company_id', '=', company_id.id)])
        if not salary_adv_obj:
            raise Warning(
                _("No Salary Advance Rule Defined For the Login User Company."))

        else:
            move_id = move_obj.create(self.account_adv_get(salary_adv_obj))
            acc_debit = salary_adv_obj.debit.id
            adv_line = {
                'type': 'src',
                'name': 'Salary Advance',
                'price_unit': self.advance,
                'price': self.advance,
                'account_id': acc_debit,
                'currency_id': self.currency_id.id,
            }
            total, adv_line = self.compute_advance_totals([adv_line])
            credit_acc = self.payment_method.default_credit_account_id.id
            adv_line.append({
                'type': 'dest',
                'name': 'Salary Advance',
                'price': total,
                'account_id': credit_acc,
                'ref': self.ids[0]
            })
            journal = move_id.journal_id
            company_currency = self.env.user.company_id.currency_id.id
            total, total_currency, adv_line = self.compute_expense_totals(self, company_currency, self.name, adv_line)
            lines = map(lambda x: (0, 0, self.line_get_convert(x, self.employee_id.address_home_id, self.date)),
                        adv_line)
            if journal.entry_posted:
                move_obj.button_validate(move_id.id)
            move_id.write({'line_id': lines})
            self.write({'state': 'approved'})

    def compute_expense_totals(self, cr, uid, adv, company_currency, ref, account_move_lines, context=None):
        cur_obj = self.pool.get('res.currency')
        total = 0.0
        total_currency = 0.0
        for i in account_move_lines:
            if adv.currency_id.id != company_currency:
                i['currency_id'] = adv.currency_id.id
                i['amount_currency'] = i['price']
                i['price'] = cur_obj.compute(cr, uid, adv.currency_id.id,
                                             company_currency, i['price'],
                                             context=context)
            else:
                i['amount_currency'] = False
                i['currency_id'] = False
            total -= i['price']
            total_currency -= i['amount_currency'] or i['price']
        return total, total_currency, account_move_lines

    @api.one
    def cancel(self):
        self.write({'state': 'cancel'})


class EmployeeAdvance(models.Model):
    _inherit = 'hr.employee'
    advance_amount = fields.Float("Advance Amount")
