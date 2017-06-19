# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.osv import osv


class SalaryStructure(models.Model):
    _inherit = 'hr.payroll.structure'
    max_percent = fields.Integer(string='Max.Salary Advance Percentage')
    advance_date = fields.Integer(string='Salary Advance-After days')


class AdvanceRule(models.Model):
    _name = "advance.rules"
    name = fields.Char(string='Name', required=True)
    debit = fields.Many2one('account.account', string='Debit Account', domain="[('type','=','other')]", required=True)
    credit = fields.Many2one('account.account', string='Credit Account', domain="[('type','=','other')]", required=True)
    journal = fields.Many2one('account.journal', string='Journal', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    analytic_journal = fields.Many2one('account.analytic.journal', string='Analytic Journal')

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id')
        advance_rule_search = self.search([('company_id', '=', company_id)])
        if advance_rule_search:
            raise osv.except_osv('Error!', 'Advance rule for this Company already exist')
        res_id = super(AdvanceRule, self).create(vals)
        return res_id

    @api.multi
    def write(self, vals):
        company_id = self.company_id
        if 'company_id' in vals:
            company_id = vals.get('company_id')
        advance_rule_search = self.search([('company_id', '=', company_id)])
        if advance_rule_search and advance_rule_search.id != self.id:
            raise osv.except_osv('Error!', 'Advance rule for this Company already exist')
        super(AdvanceRule, self).write(vals)
        return True
