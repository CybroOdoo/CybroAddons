# -*- coding: utf-8 -*-

from odoo import api, models, fields

class FirstNameLastName(models.Model):
    _inherit = 'res.partner'

    first_name = fields.Char(string='First Name', compute='_compute_first_name', readonly=False)
    last_name = fields.Char(string='Last Name', compute='_compute_last_name', readonly=False)
    nick_name = fields.Char(string='Nick Name')

    @api.onchange('last_name', 'first_name')
    def _onchange_first_last_name(self):
        if self.first_name and self.last_name:
            self.name = (self.first_name + ' ' + self.last_name)

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            name = self.name
            list = name.split(' ', 1)
            self.first_name = list[0]
            self.last_name = list[1]

    @api.depends('name')
    def _compute_first_name(self):
        if self.name:
            name = self.name
            list = name.split(' ', 1)
            self.first_name = list[0]

    @api.depends('name')
    def _compute_last_name(self):
        if self.name:
            name = self.name
            list = name.split(' ', 1)
            self.last_name = list[1]
