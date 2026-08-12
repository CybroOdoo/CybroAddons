# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

class ResConfigSettings(models.TransientModel):
    """
    Inherits res.config.settings to expose POS restriction fields in the settings UI.
    """
    _inherit = 'res.config.settings'

    pos_restaurant_restriction = fields.Boolean(
        related='pos_config_id.pos_restaurant_restriction', readonly=False, help="Enable restriction on some operations once the order has been sent to the kitchen")
    pos_orderline_quantity_update = fields.Boolean(
        related='pos_config_id.pos_orderline_quantity_update', readonly=False, help="Require manager approval to update orderline quantity")
    pos_orderline_delete = fields.Boolean(
        related='pos_config_id.pos_orderline_delete', readonly=False, help="Require manager approval to delete an orderline")
    pos_order_delete = fields.Boolean(
        related='pos_config_id.pos_order_delete', readonly=False, help="Require manager approval to delete an order")
    pos_session_close = fields.Boolean(
        related='pos_config_id.pos_session_close', readonly=False, help="Require manager approval to close the POS session")
