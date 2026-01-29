# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResCompany(models.Model):
    """Introduce watermark in pdf reports"""
    _inherit = 'res.company'

    watermark = fields.Boolean(string='Watermark', help='Enable it, while you '
                                                        'want to apply '
                                                        'watermark on your '
                                                        'pdf reports')
    content_text = fields.Char(string='Text', help="Have the text here")
    watermark_type = fields.Selection([
        ('image', 'Image'),
        ('text', 'Text'),
        ('logo', 'Logo'),
    ], default='text', help='Select the watermark type')
    color_picker = fields.Char(string='Color Picker', help='Select the Color')
    font_size = fields.Integer(string='Font size', default=30,
                               help="Mention the font size")
    background_image = fields.Image(string='Image', help='Select the image')
    rotating_angle = fields.Float(string='Angle of Rotation',
                                  help='Mention the angle of rotation')

    @api.constrains('font_size')
    def _constrains_font_size(self):
        """For limit in font size of watermark"""
        if self.font_size < 30:
            raise UserError(_("Minimum Font Size is 30"))
        if self.font_size > 131:
            raise UserError(_("Maximum Font Size is 130"))
