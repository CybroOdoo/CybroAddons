from odoo import models, fields, api, _


class AccConfig(models.TransientModel):
    _inherit = 'account.config.settings'

    loan_approve = fields.Boolean(default=False, string="Approval from Accounting Department",
                                  help="Loan Approval from account manager")

    @api.multi
    def set_loan_approve(self):
        return self.env['ir.values'].sudo().set_default(
            'account.config.settings', 'loan_approve', self.loan_approve)
