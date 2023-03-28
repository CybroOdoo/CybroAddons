# -*- coding: utf-8 -*-

from odoo import models, fields


class PosConfig(models.Model):

    _inherit = 'pos.config'

    refund_security = fields.Integer(string='Refund Security')


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    global_refund_security = fields.Integer(string='Global Refund Security',config_parameter='pos_refund_password.global_refund_security')

