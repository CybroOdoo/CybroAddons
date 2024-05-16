# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad TK (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models, _


class AccountMove(models.Model):
    """Inherit account_move for adding cleaning_id to get invoices"""
    _inherit = "account.move"

    cleaning_id = fields.Many2one("cleaning.booking",
                                  string='Cleaning',
                                  help="Choose Cleaning Management")

    def _invoice_paid_hook(self):
        """Function for getting chatter activity for invoice"""
        res = super(AccountMove, self)._invoice_paid_hook()
        [rec.cleaning_id.message_post(
            body=_('Invoice %s paid', rec._get_html_link()))
            for rec in self if
            rec.cleaning_id and rec.payment_state == 'paid']
        return res
