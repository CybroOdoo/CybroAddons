# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
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
