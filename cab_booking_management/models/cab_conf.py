# -*- coding: utf-8 -*-

from odoo import models, fields


class CabConfiguration(models.Model):
    _name = 'cab.configuration'
    _rec_name = 'cab_manager'

    auto_approve = fields.Boolean(string="Auto Approve")
    cab_manager = fields.Many2one('res.users', string='Manager', required=True)
