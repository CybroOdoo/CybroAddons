# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen(odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    """This class inherits 'res.company' and adds so_double_validation,
    so_double_validation_limit to add validation limits"""
    _inherit = 'res.company'

    so_double_validation = fields.Selection([
        ('one_step', 'Confirm sale orders in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a sale order')
    ], string="Levels of Approvals", default='one_step',
        help="Provide a double validation mechanism for sales discount.")
    so_double_validation_limit = fields.Float(
        string="Percentage of Discount that requires double validation'",
        help="Minimum discount percentage for which a double validation is "
             "required.")
