# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnuraj P(odoo@cybrosys.com)
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
from odoo.exceptions import AccessError


class MergePicking(models.TransientModel):
    """
    Class for wizard to show selected pickings to merge
    Method:
        action_merge(self):
            Method to merge the selected pickings
    """
    _name = 'merge.picking'
    _description = "Merge Picking Wizard"

    merge_picking_ids = fields.Many2many('stock.picking', string='Orders',
                                         help="Selected orders")
    existing_pick_id = fields.Many2one(
        'stock.picking', string="Merge to existing",
        help="Select a pick if you want to merge pickings to a existing picking"
             " else leave it as empty")

    def action_merge(self):
        """
        Main method to merge selected pickings
        - If checked 'merge to existing' then the selected pickings will be
          merged to last record
        - Else a new record will be created with the existing picking lines
        - The selected pickings will be moved to cancelled state
        - The newly created picking will be in ready state
        """
        # Checking for exceptions if exist raise corresponding messages
        if len(list(set(x.partner_id if x.partner_id else None for x in
                        self.merge_picking_ids))) > 1:
            raise AccessError(_("Merging is not allowed on Different partners,"
                                " please add same partner's orders"))
        if len(list(set(self.merge_picking_ids.mapped('picking_type_id')))) > 1:
            raise AccessError(
                _("Merging is not allowed on Different picking type,"
                  " please choose same type"))
        if any(state in ['done', 'cancel'] for state in
               self.merge_picking_ids.mapped('state')):
            raise AccessError(_('Merging is not allowed on Done/Cancelled '
                                'pickings, so please remove them and continue'))
        if len(list(set(self.merge_picking_ids.mapped('state')))) > 1:
            raise AccessError(_('Merging is not allowed on Different State '
                                'Pickings, please add orders in same State'))
        if len(self.merge_picking_ids) == 1:
            raise AccessError(_('Merging is not allowed on Single picking,'
                                ' please add minimum Two'))
        # If there is no exception, continues with the merging process
        source_document = []
        if self.existing_pick_id:
            main_pick = self.existing_pick_id
            orders = self.merge_picking_ids-main_pick
            moves = main_pick.move_ids
            source_document.append(main_pick.name)
        else:
            orders = self.merge_picking_ids
            moves = self.env['stock.move']
            main_pick = orders[0].copy({'move_ids': None})
        for record in orders:
            for line in record.move_ids:
                moves += line.copy({'picking_id': main_pick.id})
            source_document.append(record.name)
            record.action_cancel()
        main_pick.write(
            {'origin': f"Merged ({(', '.join(source_document))})"})
        main_pick.action_confirm()
