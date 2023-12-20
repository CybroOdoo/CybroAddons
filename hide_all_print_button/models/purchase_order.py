# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K(<https://www.cybrosys.com>)
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
from odoo import api, models


class PurchaseOrder(models.Model):
    """Class for inherited model purchase.order.
    Methods:
        fields_view_get(self, view_type):
            Function to make print button invisible according to the boolean
            field in res.users."""
    _inherit = 'purchase.order'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        """ Function to make print button invisible according to the
                    boolean field in res.users.
                view_type(list): List of views and ids
                options(dict): Dictionary of action_id,load_filters,and toolbar
                boolean:returns true."""
        res = super(PurchaseOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if ((view_type in ['tree', 'form'] and self.env.user.has_group(
                'hide_all_print_button.hide_all_print_button_group_purchase')
                and not self.env.is_admin()) and
                res['toolbar'].get('print', [])):
            res['toolbar'].get('print', []).clear()
        return res
