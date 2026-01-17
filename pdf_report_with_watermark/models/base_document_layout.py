# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anupriya Ashok (odoo@cybrosys.com)
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
from odoo import fields, models


class BaseDocumentLayout(models.TransientModel):
    """Extends the base document layout wizard to support company-level
    watermark and background configuration for PDF reports.
    These settings are dynamically fetched from the related company
    to ensure consistent report styling across the system.
    """
    _inherit = 'base.document.layout'

    watermark = fields.Boolean(related='company_id.watermark',string='Watermark',
                               help='Enable it, if you want to apply watermark '
                                    'on all your pdf reports'
                               )
    content_text = fields.Char(related='company_id.content_text',string='Content Text',
                               help="Enter the text You want to display")
    watermark_type = fields.Selection(related='company_id.watermark_type', string='Watermark Type',
                                      help='Select the Type of watermark')
    color_picker = fields.Char(related='company_id.color_picker', string='Color Picker',
                               help='Select the Color')
    font_size = fields.Integer(related='company_id.font_size', string='Font Size',
                               help="Enter the font size for the text")
    background_image = fields.Image(related='company_id.background_image',string='Background Image',
                                    help='Set an image to display')
    rotating_angle = fields.Float(related='company_id.rotating_angle', string='Rotating Angle',
                                  help='Enter the angle of rotation')
