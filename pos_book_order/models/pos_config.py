# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfig(models.Model):
    """POS configuration settings"""
    _inherit = 'pos.config'

    enable = fields.Boolean("Enable Book Orders")
