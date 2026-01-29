# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    """Inherit res users and added new fields"""
    _inherit = 'res.users'

    refund = fields.Boolean(string="Refund", help="To hide refund in pos "
                                                  "session")
    price = fields.Boolean(string="Price", help="To hide price in pos "
                                                "session")
    discount = fields.Boolean(string="Discount", help="To hide discount in pos"
                                                      "session")
    rewards = fields.Boolean(string="Rewards", help="To hide rewards in pos "
                                                    "session")
