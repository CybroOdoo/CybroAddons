# -*- coding: utf-8 -*-

from odoo import api, models, fields

class FirstNameLastName(models.Model):
    _inherit = 'res.partner'

    gender = fields.Selection([ ('male', 'Male'),
                                ('female', 'Female'),
                                ('other', 'Others')],
                                string='Gender')
