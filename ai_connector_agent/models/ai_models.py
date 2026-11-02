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


class AIModel(models.Model):
    """Store metadata for AI models fetched from configured providers."""

    _name = 'ai.model'
    _description = 'AI Model'
    _rec_name = 'model_ref_id'

    model_ref_id = fields.Char(
        string="Model Name",
        help="The unique identifier for the AI model (e.g. gpt-4o, gemini-1.5-pro)."
    )
    display_label = fields.Char(
        string="Display Name",
        help="The human-readable display name or object type for this model."
    )
    version = fields.Char(
        string="Version",
        help="The specific version of the model, if provided by the API."
    )
    owned_by = fields.Char(
        string="Owner",
        help="The organization or entity that owns the model."
    )
