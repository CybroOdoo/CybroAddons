# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
###################################################################################
from odoo import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.config'

    control_discount = fields.Boolean(string='Control Discount')
    control_price = fields.Boolean(string='Control Price')
