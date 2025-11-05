##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Maintainer: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#############################################################################

from odoo import models, fields, api


class LabRequestInvoices(models.Model):
    _inherit = 'account.invoice'

    is_lab_invoice = fields.Boolean(string="Is Lab Invoice")
    lab_request = fields.Many2one('lab.appointment', string="Lab Appointment", help="Source Document")

    @api.multi
    def action_invoice_paid(self):
        res = super(LabRequestInvoices, self).action_invoice_paid()
        lab_app_obj = self.env['lab.appointment'].search([('id', '=', self.lab_request.id)])
        for obj in lab_app_obj:
            obj.write({'state': 'invoiced'})
        return res
