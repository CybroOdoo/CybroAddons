# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
from odoo import fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    """Class to add new field in purchase order"""
    _inherit = 'purchase.order'

    requisition_order = fields.Char(                                    help='Set a requisition Order')

    def action_print_requisition_report(self):
        """Print the purchase requisition report of the linked requisition"""
        requisitions = self.env['employee.purchase.requisition'].search([
            ('name', 'in', self.mapped('requisition_order'))])
        if not requisitions:
            raise UserError(self.env._('No purchase requisition is linked to the '
                              'selected purchase order(s).'))
        return requisitions.action_print_report()
