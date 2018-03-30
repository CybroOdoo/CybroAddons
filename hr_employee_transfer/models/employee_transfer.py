# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class EmployeeTransfer(models.Model):
    _name = 'employee.transfer'
    _description = 'Employee Transfer'
    _order = "id desc"

    def _default_employee(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    name = fields.Char(string='Name', help='Give a name to the Transfer', copy=False, default="/")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date = fields.Date(string='Date', default=fields.Date.today())
    branch = fields.Many2one('transfer.company', string='Transfer Branch', requried=True, copy=False)
    state = fields.Selection(
        [('draft', 'New'), ('cancel', 'Cancelled'), ('transfer', 'Transferred'), ('done', 'Post')],
        string='Status', readonly=True, copy=False, default='draft')
    sequence_number = fields.Integer(string='Sequence Number', help='A unique sequence number for the Transfer',
                                     default=1, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 related='employee_id.company_id', store=True)
    note = fields.Text(string='Internal Notes')
    responsible = fields.Many2one('hr.employee', string='Responsible', default=_default_employee, readonly=True)

    @api.one
    def transfer(self):
        obj_emp = self.env['hr.employee'].browse(self.employee_id.id)
        emp = {}
        for this in self:
            emp = {
                'name': self.employee_id.name,
                'company_id': self.branch.company_id,

            }
        new_emp = self.env['hr.employee'].create(emp)
        if obj_emp.address_home_id:
            obj_emp.address_home_id.active = False
        for obj_contract in self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)]):
            if obj_contract.date_end:
                continue
            if not obj_contract.date_end:
                obj_contract.write({'date_end': date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)})
                self.wage = obj_contract.wage
        self.state = 'transfer'
        self.employee_id = new_emp
        obj_emp.write({'active': False})

    @api.multi
    def receive_employee(self):
        print self.employee_id.company_id.id
        for this in self:
            if this._context is None:
                context = {}
            partner = {}
            for i in this:
                partner = {
                    'name': i.employee_id.name,
                    'company_id': i.branch.company_id,
                }
            partner_created = self.env['res.partner'].create(partner)
            self.env['hr.employee'].browse(this.employee_id.id).write({'address_home_id': partner_created.id})
            return {
                'name': _('Contract'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.contract',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': {'default_employee_id': this.employee_id.id,
                            'default_date_start': this.date,
                            'default_emp_transfer': this.id,
                            },
            }

    @api.one
    def cancel_transfer(self):
        obj_emp = self.env['hr.employee'].browse(self.employee_id.id)
        emp = {
            'name': self.employee_id.name,
            'company_id': self.company_id.id,
        }
        obj_emp.write(emp)
        for obj_contract in self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)]):
            obj_contract.unlink()
        self.state = 'cancel'
