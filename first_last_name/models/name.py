# -*- coding: utf-8 -*-

from odoo import api, models, fields

class FirstNameLastName(models.Model):
    _inherit = 'res.partner'

    first_name = fields.Char(string='First Name', compute='_compute_first_name', readonly=False)
    last_name = fields.Char(string='Last Name', compute='_compute_last_name', readonly=False)
    nick_name = fields.Char(string='Nick Name')

    @api.onchange('last_name', 'first_name')
    def _onchange_first_last_name(self):
        print(self)
        print("_onchange_first_last_name")
        print(self.name)
        print(self.first_name)
        print(self.last_name)
        if self.first_name and self.last_name:
            self.name = (self.first_name + ' ' + self.last_name)

    @api.onchange('name')
    def _onchange_name(self):
        print(self)
        print("_onchange_name")
        if self.name and self.company_type == 'person':
            name = self.name
            list = name.split(' ', 1)
            print(list)
            self.first_name = list[0]
            self.last_name = list[1]

    @api.depends('name')
    def _compute_first_name(self):
        print("_compute_first_name")
        for i in self:
            list = i.name.split(' ',1) if i.name else None
            if list and i.company_type == 'person':
                i.first_name = list[0]

    @api.depends('name')
    def _compute_last_name(self):
        print("_compute_last_name")
        for i in self:
            list = i.name.split(' ', 1)  if i.name else None
            print(list)
            if list and i.company_type == 'person':
                print(i.name)
                i.last_name = list[1]