# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields
from odoo.exceptions import ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)
    bank_reference = fields.Char(copy=False)
    cheque_reference = fields.Char(copy=False)

    def _create_payment_vals_from_wizard(self):

        res = super(AccountPaymentRegister,
                    self)._create_payment_vals_from_wizard()
        res.update({'effective_date': self.effective_date,
                    'cheque_reference': self.cheque_reference,
                    'bank_reference': self.bank_reference})
        if not res['effective_date'] and self.payment_method_code == 'pdc':
            raise ValidationError("Please choose an Effective Date.")
        return res
