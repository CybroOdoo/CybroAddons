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


class Website(models.Model):
    """Inheriting website to add new fields"""
    _inherit = 'website'

    under_maintenance = fields.Boolean(string="Under Maintenance",
                                       help="Enable or disable to show "
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
