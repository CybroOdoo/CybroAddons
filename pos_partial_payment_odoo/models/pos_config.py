# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj(odoo@cybrosys.info)
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
from odoo import models, fields


class PosConfig(models.Model):
    """
    This class extends the 'pos.config' model to add the 'partial_payment' field

    The 'partial_payment' field allows configuring whether the Point of Sale
    (POS) system should allow partial payments for orders.
    """
    _inherit = 'pos.config'

    partial_payment = fields.Boolean(string='Allow Partial Payment',
                                     default=True,
                                     help="If enabled, the Point of Sale system"
                                          "allows partial payments for orders.")
