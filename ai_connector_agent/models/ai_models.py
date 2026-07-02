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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields


class AIModel(models.Model):
    """Store metadata for AI models fetched from configured providers."""

    _name = 'ai.model'
    _description = 'AI Model'
    _rec_name = 'modelId'

    modelId = fields.Char(string="Model Name", help="The unique identifier for the AI model (e.g. gpt-4o, gemini-1.5-pro).")
    object = fields.Char(string="Object", help="The type of object the model represents, or its display name.")
    version = fields.Char(string="Version", help="The specific version of the model, if provided by the API.")
    createdId = fields.Char(string="Created", help="The timestamp or ID when this model record was first discovered.")
    owned_by = fields.Char(string="Owner", help="The organization or entity that owns the model.")
