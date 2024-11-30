from odoo import models


class AccountPaymentRegister(models.TransientModel):
    """Alter loan repayment line state based on invoice status"""
    _inherit = 'account.payment.register'

    def _post_payments(self, to_process, edit_mode=False):
        """Change repayment record state to 'paid' while registering the
        payment"""
        res = super()._post_payments(to_process, edit_mode=False)
        for record in self:
            loan_line_id = self.env['repayment.line'].search([
                ('name', 'ilike', record.communication)])
            loan_line_id.write({'state': 'paid'})
        return res