# -*- coding: utf-8 -*-

from openerp import models, fields


class WebsiteMapkey(models.Model):
    _inherit = 'website'
    map_key = fields.Char("Map Embed URL")


class WebsiteMapConfig(models.Model):
    _inherit = 'website.config.settings'

    map_key = fields.Char(related='website_id.map_key', string="Map Embed URL",
                          help="Paste your google map embed URL here. Only paste the src of iframe here")
