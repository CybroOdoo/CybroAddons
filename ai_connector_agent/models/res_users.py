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

class ResUsers(models.Model):
    """Extend users with active AI provider and model preferences."""

    _inherit = 'res.users'

    active_ai_agent_id = fields.Many2one('ai.provider', string="Active AI Agent", help="The user's preferred AI Agent or Provider, used to initialize the chat interface.")
    active_ai_model_id = fields.Many2one('ai.model', string="Active AI Model", help="The user's preferred AI Model, used alongside the Active AI Agent.")
