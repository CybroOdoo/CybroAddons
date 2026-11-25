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


class ResUsers(models.Model):
    """Inherit res.users to add discount control fields."""
    _inherit = 'res.users'

    is_discount_control = fields.Boolean(
        string='Discount Control',
        help='Identify whether discount control is applied to this user.',
    )
    allow_discount = fields.Float(
        string='Allowed Discount (%)',
        help='Maximum allowed discount percentage limit for the user.',
    )
