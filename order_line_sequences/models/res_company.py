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
from odoo import fields, models


class ResCompany(models.Model):
    """Inherit res.company to default show_sol_numbers to True."""

    _inherit = 'res.company'

    show_sol_numbers = fields.Boolean(default=True)

    def _auto_init(self):
        res = super()._auto_init()
        self.env['res.company'].search(
            [('show_sol_numbers', '=', False)],
        ).write({'show_sol_numbers': True})
        return res
