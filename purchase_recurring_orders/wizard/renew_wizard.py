# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from openerp import models, fields, api


class RenewWizard(models.TransientModel):
    _name = "purchase.recurring_orders.renew_wizard"

    def _get_renewal_date(self):
        agreements = self.env['purchase.recurring_orders.agreement'].browse(
            self.env.context.get('active_ids', []))
        return agreements[:1].next_expiration_date

    date = fields.Date(
        string='Renewal date', required=True,
        help="Effective date of the renewal. This date is the one taken into "
             "account in the next renewal",
        default=_get_renewal_date)
    comments = fields.Char(
        string='Comments', size=200, help='Renewal comments')

    @api.multi
    def create_renewal(self, cr, uid, ids, context=None):
        self.ensure_one()
        agreement_ids = context.get('active_ids', [])
        for agreement_id in agreement_ids:
            self.env['purchase.recurring_orders.agreement.renewal'].create(
                {'agreement_id': agreement_id,
                 'date': self.date,
                 'comments': self.comments})
        agreement_model = self.env['purchase.recurring_orders.agreement']
        agreement_model.browse(agreement_ids).write(
            {'last_renovation_date': self.date,
             'renewal_state': 'renewed'})
        return True
