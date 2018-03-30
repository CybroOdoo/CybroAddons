# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EmployeeTransfer(models.Model):
    _name = 'transfer.company'
    _description = 'Transfer Company'
    _order = "id desc"

    name = fields.Char(string='Name', copy=False, ondelete='cascade')
    company_id = fields.Integer(string='Company', help='Company name same as res.company', copy=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    def init(self):
        obj_company = self.env['res.company'].search([])

        for company in obj_company:
            obj_branch = self.env['transfer.company'].search([('company_id', '=', company.id)])
            com = {}
            if not obj_branch:
                com = {
                    'name': company.name,
                    'company_id': company.id,
                }
                obj = self.env['transfer.company'].create(com)

    @api.model
    def create(self, res):
        result = super(ResCompany, self).create(res)
        com = {}
        com = {
                'name': result.name,
                'company_id': result.id,

            }
        self.env['transfer.company'].create(com)
        return result
