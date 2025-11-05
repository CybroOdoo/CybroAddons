# -*- coding: utf-8 -*-

from odoo import models, fields


class PosLockConfig(models.Model):
    _inherit = 'pos.config'

    pos_lock = fields.Boolean(string='Enable Lock Screen')
    bg_color = fields.Char('Background Color', default='rgb(218, 218, 218)',
                           help='The background color of the lock screen, '
                                '(must be specified in a html-compatible format)')
