# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Choose the voice assistant of the shop page"""
    _inherit = 'res.config.settings'

    is_website_assistant = fields.Boolean(
        string='Enable Website Assistant',
        config_parameter='ora_ai_website.is_website_assistant',
        help='Show the voice assistant on the shop page of the website.')
    website_assistant_id = fields.Many2one(
        'ora.ai', string='Choose Assistant',
        config_parameter='ora_ai_website.website_assistant_id',
        domain="[('state', '=', 'done')]",
        help='Assistant the website visitors talk to. Only the assistants '
             'created on Vapi can be chosen.')
