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


class ResConfigSettings(models.TransientModel):
    """Configure AI image generation providers and default settings."""
    _inherit = 'res.config.settings'

    # Brand DNA — must be Char, not Text (res.config.settings only supports
    # boolean, integer, float, char, selection, many2one, datetime with config_parameter)
    ai_brand_dna = fields.Char(
        string='Brand DNA / Visual Style Guide',
        help='Describe your brand visual identity. This is prepended to every AI prompt to ensure consistent imagery.',
        config_parameter='smart_product_image_generator.brand_dna',
    )

    # API Keys
    openai_api_key = fields.Char(
        string='OpenAI API Key',
        help='Your OpenAI API key for DALL-E 3 image generation.',
        config_parameter='smart_product_image_generator.openai_api_key',
    )
    stability_api_key = fields.Char(
        string='Stability AI API Key',
        help='Your Stability AI API key for image generation.',
        config_parameter='smart_product_image_generator.stability_api_key',
    )
    gemini_api_key = fields.Char(
        string='Google Gemini API Key',
        help='Your Google Gemini API key for image generation.',
        config_parameter='smart_product_image_generator.gemini_api_key',
    )

    # Approval workflow
    ai_approval_required = fields.Boolean(
        string='Require Manager Approval',
        help='When enabled, generated images must be approved by a manager before being applied to products.',
        config_parameter='smart_product_image_generator.approval_required',
    )

    # Default variants
    ai_max_variants = fields.Integer(
        string='Default Number of Variants',
        help='Default number of image variants to generate (max 4).',
        config_parameter='smart_product_image_generator.max_variants',
        default=4,
    )
