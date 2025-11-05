# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Website(models.Model):
    _inherit = "website"

    hotjar_analytics_script = fields.Text('Hotjar Analytics Script')
