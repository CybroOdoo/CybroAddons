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


class PosConfig(models.Model):
    """Inherit POS configuration to add store physical address for Click & Collect pickup."""
    _inherit = 'pos.config'

    street = fields.Char(help='Street address for your store.')
    street2 = fields.Char(help='Additional street address details.')
    zip = fields.Char(string='ZIP', help='Postal code of the store.')
    city = fields.Char(help='City where the store is located.')
    state_id = fields.Many2one("res.country.state",
                               help='State or province where the store is located.')
    country_id = fields.Many2one('res.country',
                                 help='Country where the store is located.')
