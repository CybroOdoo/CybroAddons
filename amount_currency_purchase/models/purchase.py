# -*- coding: utf-8 -*-

import re

from odoo import api, models, fields, _

class PurchaseCurrency(models.Model):
    _inherit = 'purchase.order'

    company_currency_amount = fields.Float(string='Company Currency Total', compute='find_amount')

    def find_amount(self):
        for this in self:
            price = self.env['res.currency']._compute(this.currency_id, this.company_id.currency_id, this.amount_total)
            this.company_currency_amount = price

