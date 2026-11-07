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


class ResPartner(models.Model):
    """Inherited the module res.partner to add the following fields, which
    indicate the referral code, points and no: of signups happened by
    using their referral code"""
    _inherit = 'res.partner'

    referral_code = fields.Char(string="Referral Code", help="Referral code",
                                readonly=True)
    points = fields.Integer(string='Points', help='Points acquired',
                            default=0, readonly=True)
    sign_up = fields.Integer(string='Signups',
                             help='Shows number of signup happens by using your'
                                  'referral code', default=0, readonly=True)
