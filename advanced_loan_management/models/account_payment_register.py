# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Megha (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
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
