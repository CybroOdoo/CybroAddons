# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj(odoo@cybrosys.com)
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


class ResPartner(models.Model):
    """Inherited to add provider_ids field"""
    _inherit = 'res.partner'

    provider_ids = fields.Many2many('payment.acquirer',
                                    string='Payment Acquirer',
                                    help='The selected payment acquirers will '
                                         'be visible at website payment page '
                                         'along with the public payment '
                                         'acquirers.',
                                    domain=lambda self: [('state', 'in',
                                                          ['enabled', 'test'])])
