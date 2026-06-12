# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class ResConfSettings(models.TransientModel):
    """Fields adds to Configuration settings"""
    _inherit = 'res.config.settings'

    google_tags_manager = fields.Boolean(string='Google Tag Manager',
                                         related='website_id'
                                                 '.google_tags_manager',
                                         config_parameter='google_tag_manager'
                                                          '.google_tags_manager'
                                         ,
                                         readonly=False,
                                         help='Enable to add container id')
    container_name = fields.Char(string='Container Id',
                                 related='website_id.container_name',
                                 config_parameter='google_tag_manager'
                                                  '.container_name',
                                 readonly=False, help='Add container id')
