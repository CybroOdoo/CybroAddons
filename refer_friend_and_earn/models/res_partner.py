# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathti V (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    """Inherited the module res.partner to add the following fields, which
    indicate the referral code, points earned and no: of signups happened by
    using their referral code"""
    _inherit = 'res.partner'

    referral_code = fields.Char(string="Referral Code", help="Referral code",
                                readonly=True)
    points = fields.Integer(string='points', help='Points acquired',
                            readonly=True)
    sign_up = fields.Integer(string='signups', help='shows number of signup '
                                                    'happens by using your'
                                                    ' referral code',
                             readonly=True)
