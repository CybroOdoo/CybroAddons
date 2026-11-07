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


class Website(models.Model):
    """Inheriting website to add new fields"""
    _inherit = 'website'

    under_maintenance = fields.Boolean(help="Enable or disable to show "
                                            "maintenance page")
    maintenance_msg = fields.Char(string="Maintenance Message",
                                  help="Pass a message to load on "
                                       "maintenance page")
    maintenance_hdr = fields.Char(string="Maintenance Header",
                                  help="Display maintenance header in "
                                       "maintenance page")
    maintenance_hdr_color = fields.Char(string="Header Color",
                                        help="Choose Header Color")
    maintenance_cont_color = fields.Char(string="Content Color",
                                         help="Choose Content Color")
    maintenance_img = fields.Binary(string="Maintenance Image",
                                    help="Image to load on maintenance page")
