# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class MondayItem(models.Model):
    """Class for storing Items received from Monday.com"""
    _name = "monday.item"
    _description = "Monday Item"

    board_id = fields.Many2one('monday.board', string="Board",
                               help="This indicates the board")
    group_id = fields.Many2one('monday.group', string="Group",
                               help="This indicates the group")
    name = fields.Char(string="Item", help="ID of the item", readonly=True)
    column_value_ids = fields.One2many('item.column.value',
                                       'item_id',
                                       string="Column Value",
                                       help="It is the Column Value of the "
                                            "item")
