# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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
    """ Inhering to add a field to enable website pre-loader"""
    _inherit = 'res.config.settings'

    enable_website_pre_loader = fields.Boolean(string='Website Pre-Loader',
                                               config_parameter='website_pre_loader_style.enable_website_pre_loader',
                                               default=True,
                                               help="Enable Website pre-loader")
    loader_style = fields.Selection([('bean eater', 'Bean eater'),
                                     ('cube', 'Cube'),
                                     ('disk', 'Disk'),
                                     ('dual', 'Dual'),
                                     ('gear', 'Gear'),
                                     ('infinity', 'Infinity'),
                                     ('pulse', 'Pulse'),
                                     ('ripple', 'Ripple'),
                                     ('spinner', 'Spinner')
                                     ],
                                    config_parameter='website_pre_loader_style.loader_style',
                                    default='dual', string="Loader Style",
                                    help="Website pre-loader loading style")
