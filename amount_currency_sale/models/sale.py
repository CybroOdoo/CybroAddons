# -*- coding: utf-8 -*-
""" find the total amount in company currency """

from odoo import api, models, fields

class PurchaseCurrency(models.Model):
    """ Creates the new field to store the total amount in company currency"""
    _inherit = 'sale.order'

    company_currency_amount = fields.Float(string='Company Currency Total',
                                           compute='find_amount')
    @api.models
    def find_amount(self):
        """ Function to calculate the total amount in company currency"""
        for this in self:
            price = self.env['res.currency']._compute(this.currency_id,
                                                      this.company_id.currency_id,
                                                      this.amount_total)
            this.company_currency_amount = price
