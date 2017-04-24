# -*- coding: utf-8 -*-

from odoo import models, fields


class CabLocation(models.Model):
    _name = 'cab.location'

    name = fields.Char(string='City', required=True)
    cab_zip = fields.Char(string='ZIP')
    cab_code = fields.Char(string='City Code', size=64, help="The official code for the city")
    state_id = fields.Many2one('res.country.state', string='State', required=True)
    country_id = fields.Many2one('res.country', string='Country', required=True)

