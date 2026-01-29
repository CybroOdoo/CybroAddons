# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class ResPartner(models.Model):
    """Inherited the module res partner to add the following fields, which
    indicate the referral code, points earned and no: of signups happened by
    using their referral code"""
    _inherit = 'res.partner'

    referral_code = fields.Char(string="Referral Code", readonly=True,
                                help="Referral code of the partner")
    points = fields.Integer(string='Points', help='Points acquired',
                            readonly=True)
    sign_up = fields.Integer(string='Signups', readonly=True,
                             help='Shows number of signups happens by using'
                                  'your referral code')
