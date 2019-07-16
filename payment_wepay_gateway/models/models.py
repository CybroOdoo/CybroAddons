# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author:Cybrosys Technologies (<www.cybrosys.com>)
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
##############################################################################

import logging
from openerp import models, fields, _

_logger = logging.getLogger(__name__)


class Wepay(models.Model):
    _inherit = 'payment.acquirer'

    def _get_providers(self, cr, uid, context=None):
        providers = super(Wepay, self)._get_providers(cr, uid, context=context)
        providers.append(['wepay', 'WePay'])
        return providers
    wepay_merchant_id = fields.Char("Client Id")
    wepay_account_id = fields.Char("Account Id")
    wepay_access_tocken = fields.Char("Access Token")


class WepayTransaction(models.Model):
    _inherit = "payment.transaction"
    wepay_checkout_id = fields.Char("Wepay Checkout Id")
    acquirer_name = fields.Selection(related='acquirer_id.provider')