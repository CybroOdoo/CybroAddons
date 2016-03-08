# -*- coding: utf-8 -*-

from openerp import models, fields, api

class PosProductCateg(models.Model):

    _inherit = 'pos.config'

    available_categ = fields.Many2many('pos.category', string='Available Product Categories')

