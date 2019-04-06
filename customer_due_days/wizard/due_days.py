# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CreditDueExceedReportWizard(models.TransientModel):
    _name = 'customer.due.report'

    @api.model
    def xlsx_credit_due_report(self,data):
        data = {}
        return self.env.ref('customer_due_days.report_customer_due_xlsx').report_action(self, data=data)

