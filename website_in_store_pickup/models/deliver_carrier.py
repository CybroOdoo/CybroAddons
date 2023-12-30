# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    """Class to add the fields to identify a method as a store picking
    delivery method and choose the stores to be available for that particular
    delivery method"""
    _inherit = 'delivery.carrier'

    is_store_pick = fields.Boolean(string='In-Store Pickup',
                                   help="Enable this to identify this as an "
                                        "In-store PickUp delivery method")
    store_ids = fields.Many2many('stock.warehouse',
                                 string="Available Stores",
                                 domain="[('is_store', '=', True)]",
                                 help="Choose the stores available for "
                                      "in-store picking and if no stores "
                                      "implies all stores are available")
