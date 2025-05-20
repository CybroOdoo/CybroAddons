# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import fields, models


class ResCompany(models.Model):
    """Introduce watermark in pdf reports"""
    _inherit = 'res.company'

    watermark = fields.Boolean(string='Watermark', help='Enable it, while you '
                                                        'want to apply '
                                                        'watermark on your pdf '
                                                        'reports')
    content_text = fields.Char(string='Text', help="Have the text here")
    watermark_type = fields.Selection([
        ('image', 'Image'),
        ('text', 'Text'),
        ('logo', 'Logo'),
    ], default='text', help='Select the watermark type')
    color_picker = fields.Char(string='Color Picker', help='Select the Color')
    font_size = fields.Integer(string='Font size', default=20,
                               help="Mention the font size")
    background_image = fields.Image(string='Image', help='Select the image')
    rotating_angle = fields.Float(string='Angle of Rotation',
                                  help='Mention the angle of rotation')

class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    watermark = fields.Boolean(related='company_id.watermark')
    content_text = fields.Char(related='company_id.content_text')
    watermark_type = fields.Selection(related='company_id.watermark_type')
    color_picker = fields.Char(related='company_id.color_picker')
    font_size = fields.Integer(related='company_id.font_size')
    background_image = fields.Image(related='company_id.background_image')
    rotating_angle = fields.Float(related='company_id.rotating_angle')