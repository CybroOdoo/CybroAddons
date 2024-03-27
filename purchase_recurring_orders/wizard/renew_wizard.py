# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ayana KP (odoo@cybrosys.com)
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
from odoo import fields, models


class RenewWizard(models.TransientModel):
    _name = "agreement.renewal"
    _inherit = 'mail.thread'
    _description = "Agreement Renewal Wizard"

    def _get_renewal_date(self):
        """Method for getting the renewal date"""
        agreements = self.env['purchase.recurring.agreement'].browse(
            self.env.context.get('active_ids', []))
        return agreements[:1].next_expiration_date

    date = fields.Date(
        string='Renewal Date', required=True,
        help="Effective date of the renewal. This date is the one taken into "
             "account in the next renewal",
        default=_get_renewal_date)
    comments = fields.Char(
        string='Comments', size=200, help='Renewal comments')

    def create_renewal(self):
        """Method for renewal of purchase recurring agreement"""
        self.ensure_one()
        agreement_ids = self.env.context.get('active_ids', [])
        for agreement_id in agreement_ids:
            self.env['purchase.agreement.renewal'].create(
                {'recurring_agreement_id': agreement_id,
                 'date': self.date,
                 'comments': self.comments})
        self.env['purchase.recurring.agreement'].browse(agreement_ids).write(
            {'last_renovation_date': self.date,
             'renewal_state': 'renewed'})
        return True
