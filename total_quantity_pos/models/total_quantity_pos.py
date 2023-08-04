# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R (odoo@cybrosys.com)
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


class PosConfig(models.Model):
    """ Class for adding the fields in the pos config"""
    _inherit = "pos.config"

    pos_total_items = fields.Boolean(string="Total Items",
                                     help="The boolean field"
                                          " in pos.config respective"
                                          " to the total_items field"
                                          " in res.config.settings")
    pos_total_quantity = fields.Boolean(string="Total Quantity",
                                        help="The boolean field"
                                             " in pos.config respective"
                                             " to the total_quantity field"
                                             " in res.config.settings")


class ConfigSettings(models.TransientModel):
    """Class for adding the fields in res.config.settings"""
    _inherit = 'res.config.settings'

    total_items = fields.Boolean(string="Enable Total Items",
                                 related="pos_config_id.pos_total_items",
                                 readonly=False, help="Enable this option "
                                                      "will show the total"
                                                      " number of items and"
                                                      " total quantities of"
                                                      " product in the "
                                                      "PoS screen.")
    total_quantity = fields.Boolean(string="Enable Total Quantity",
                                    related="pos_config_id.pos_total_quantity",
                                    readonly=False, help="Enable this option "
                                                         "will show the total"
                                                         " number of items and"
                                                         " total quantities of"
                                                         " product in the"
                                                         " receipt.")
