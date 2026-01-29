# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models


class MrpProduction(models.Model):
    """ Extend the model 'mrp.production' for adding the button for split the
     manufacturing order"""
    _inherit = 'mrp.production'

    def action_split_order(self):
        """ Open wizard when click on 'split mo' button """
        work_order = self.env.user.has_group('mrp.group_mrp_routings')
        if work_order:
            context = {
                'default_order_id': self._origin.id,
                'default_works': True
            }
        else:
            context = {
                'default_order_id': self._origin.id,
            }
        return {
            'name': 'Split Order',
            'res_model': 'split.order',
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }
