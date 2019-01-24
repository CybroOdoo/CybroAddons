# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        obj_incentive = self.env['daily.target'].search([('user_id', '=', self.user_id.id), ('state', '=', 'open')])
        if obj_incentive:
            try:
                obj_target = self.env['target.day'].search([('date_today', '=', self.date_invoice),
                                                            ('incentive_id', '=', obj_incentive.id)])
                for i in obj_target:
                    i.write({'amount': i.amount + self.amount_untaxed})
                tot = obj_incentive.achieve_amount + self.amount_untaxed
                obj_incentive.write({'achieve_amount': tot})
            except Exception:
                pass
        return res

    @api.multi
    def action_invoice_cancel(self):
        res = super(AccountInvoice, self).action_invoice_cancel()
        obj_incentive = self.env['daily.target'].search([('user_id', '=', self.user_id.id), ('state', '=', 'open')])
        if obj_incentive:
            try:
                obj_target = self.env['target.day'].search([('date_today', '=', self.date_invoice),
                                                            ('incentive_id', '=', obj_incentive.id)])
                for i in obj_target:
                    day_total = i.amount - self.amount_untaxed
                    i.write({'amount': day_total})
                tot = obj_incentive.achieve_amount - self.amount_untaxed
                obj_incentive.write({'achieve_amount': tot})
            except Exception:
                pass

        return res
