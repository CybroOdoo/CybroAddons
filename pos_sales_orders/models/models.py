# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2015-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aswani P C(<https://www.cybrosys.com>)
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

from openerp import models, fields


class PosSaleOrder(models.Model):
    _inherit = 'sale.order'

    from_pos = fields.Boolean(string="Created From POS", default=False)

    def create_from_ui(self, cr, uid, orders, context=None):
        order_id = self.create(cr, uid, orders, context=context)
        order_ref = self.browse(cr, uid, order_id, context=context).name
        return order_ref

