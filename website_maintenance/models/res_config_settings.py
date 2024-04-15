# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inheriting ResConfigSettings Model.
        This class extends the functionality of the 'res.config.settings'
        model.It allows customizing and managing configuration settings
        for the module"""
    _inherit = 'res.config.settings'

    is_under_maintenance = fields.Boolean(
        string="Under Maintenance",
        related="website_id.under_maintenance",
        readonly=False,
        help="Enable or disable to show Maintenance page")
    maintenance_header = fields.Char(string="Maintenance Header",
                                     related="website_id.maintenance_hdr",
                                     readonly=False,
                                     help="Add Maintenance header to show "
                                          "on the website")
    maintenance_hdr_color = fields.Char(string="Header Color",
                                        related="website_id."
                                                "maintenance_hdr_color",
                                        readonly=False,
                                        help="Choose Header Color")
    maintenance_cont_color = fields.Char(string="Content Color",
                                         related="website_id."
                                                 "maintenance_cont_color",
                                         readonly=False,
                                         help="Choose Content Color")
    maintenance_message = fields.Char(string="Maintenance Info",
                                      related="website_id.maintenance_msg",
                                      readonly=False,
                                      help="Add Maintenance message "
                                           "regarding scheduled days/"
                                           "available options/reason etc")
    maintenance_img = fields.Binary(string="Maintenance Image",
                                    related="website_id.maintenance_img",
                                    readonly=False,
                                    help="Display an image to show on "
                                         "the maintenance page")
