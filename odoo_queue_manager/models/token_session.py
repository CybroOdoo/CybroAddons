# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class TokenSession(models.Model):
    """Model representing a Token Session"""
    _name = 'token.session'
    _description = 'Token Session'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string='Order Reference', readonly=True,
                               copy=False, help='Sequence number',
                               default=lambda self: self.env._('New'))
    name = fields.Char(help='Name of the session')
    opened_by = fields.Many2one('res.users', help='Who started the session',
                            default=lambda self: self.env.uid, readonly=True)
    opened_datetime = fields.Datetime(string='Opened Time', readonly=True, index=True, default=fields.Datetime.now)

    @api.model_create_multi
    def create(self, vals_list):
        """This function create the reference number"""
        for vals in vals_list:
            if vals.get('reference_no', self.env._('New')) == self.env._('New'):
                vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                    'token.session') or self.env._('New')
        return super().create(vals_list)
