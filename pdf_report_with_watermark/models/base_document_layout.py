# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (odoo@cybrosys.com)
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
    _inherit = 'base.document.layout'

    watermark = fields.Boolean(related='company_id.watermark',
                               help='Enable it, if you want to apply watermark '
                                    'on all your pdf reports'
                               )
    content_text = fields.Char(related='company_id.content_text',
                               help="Enter the text You want to display")
    watermark_type = fields.Selection(related='company_id.watermark_type',
                                      help='Select the Type of watermark')
    color_picker = fields.Char(related='company_id.color_picker',
                               help='Select the Color')
    font_size = fields.Integer(related='company_id.font_size',
                               help="Enter the font size for the text")
    background_image = fields.Image(related='company_id.background_image',
                                    help='Set an image to display')
    rotating_angle = fields.Float(related='company_id.rotating_angle',
                                  help='Enter the angle of rotation')
