# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import api, fields, models
from odoo.exceptions import AccessDenied


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    has_hotjar_analytics = fields.Boolean("Hotjar Analytics")
    hotjar_analytics_script = fields.Text('Hotjar Analytics Script', related='website_id.hotjar_analytics_script')

    @api.onchange('has_hotjar_analytics')
    def onchange_has_hotjar_analytics(self):
        if not self.has_hotjar_analytics:
            self.hotjar_analytics_script = False

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            has_hotjar_analytics=get_param('website.has_hotjar_analytics'),
        )
        return res

    def set_values(self):
        if not self.user_has_groups('website.group_website_designer'):
            raise AccessDenied()
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.has_hotjar_analytics', self.has_hotjar_analytics)
