# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    unique_id = fields.Char(string='Unique Id', help="The Unique Sequence no", readonly=True, default='/')

    @api.model
    def create(self, values):
        res = super(ResPartner, self).create(values)
        company_seq = self.env['res.users'].browse(self._uid).company_id
        if res.customer and res.unique_id == '/':
            if company_seq.next_code:
                res.unique_id = company_seq.next_code
                res.name = '[' + str(company_seq.next_code) + ']' + str(res.name)
                company_seq.write({'next_code': company_seq.next_code + 1})
            else:
                res.unique_id = company_seq.customer_code
                res.name = '[' + str(company_seq.customer_code) + ']' + str(res.name)
                company_seq.write({'next_code': company_seq.customer_code + 1})
        if res.supplier == True and res.unique_id == '/':
            if company_seq.supp_code < 10:
                res.unique_id = '000' + str(company_seq.supp_code)
                res.name = '[' + '000' + str(company_seq.supp_code) + ']' + str(res.name)
                company_seq.write({'supp_code': company_seq.supp_code + 1})
            elif company_seq.supp_code < 100:
                res.unique_id = '00' + str(company_seq.supp_code)
                res.name = '[' + '00' + str(company_seq.supp_code) + ']' + str(res.name)
                company_seq.write({'supp_code': company_seq.supp_code + 1})
            elif company_seq.supp_code < 1000:
                res.unique_id = '0' + str(company_seq.supp_code)
                res.name = '[' + '0' + str(company_seq.supp_code) + ']' + str(res.name)
                company_seq.write({'supp_code': company_seq.supp_code + 1})
            elif company_seq.supp_code > 1000:
                res.unique_id = company_seq.supp_code
                res.name = '[' + str(company_seq.supp_code) + ']' + str(res.name)
                company_seq.write({'supp_code': company_seq.supp_code + 1})
            else:
                res.unique_id = company_seq.supp_code
                res.name = '[' + '0001' + ']' + str(res.name)
                company_seq.write({'supp_code': 2})
        return res
