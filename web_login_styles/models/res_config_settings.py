# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    orientation = fields.Selection([('default', 'Default'), ('left', 'Left'), ('middle', 'Middle'), ('right', 'Right')], string="Orientation")
    background = fields.Selection([('color', 'Color Picker'), ('image', 'Image'), ('url', 'URL')], string="Background")
    image = fields.Binary(string="Image")
    url = fields.Char(string="URL")
    color = fields.Char(string="Color")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            background=params.get_param('web_login_styles.background'),
            orientation=params.get_param('web_login_styles.orientation'),
            image=params.get_param('web_login_styles.image'),
            url=params.get_param('web_login_styles.url'),
            color=params.get_param('web_login_styles.color'),
        )

        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        set_orientation = self.orientation or False
        set_image = self.image or False
        set_url = self.url or False
        set_color = self.color or False
        set_background = self.background or False
        params.set_param('web_login_styles.background', set_background)
        params.set_param('web_login_styles.orientation', set_orientation)
        params.set_param('web_login_styles.image', set_image)
        params.set_param('web_login_styles.url', set_url)
        params.set_param('web_login_styles.color', set_color)

    @api.onchange('orientation')
    def onchange_orientation(self):
        if self.orientation == 'default':
            self.background = False
