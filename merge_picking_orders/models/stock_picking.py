# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnuraj (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models, _


class StockPicking(models.Model):
    """
    Inherit Pickings class for add merge orders action function,
    Method:
         action_merge_picking(self):
            Create new wizard with selected records
    """
    _inherit = 'stock.picking'

    def action_merge_picking(self):
        """ Method create wizard for select pickings """
        merge_picking = self.env['merge.picking'].create({
            'merge_picking_ids': [fields.Command.set(self.ids)],
        })
        return {
            'name': _('Merge Picking Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'merge.picking',
            'view_mode': 'form',
            'res_id': merge_picking.id,
            'target': 'new'
        }
