# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo import fields, models


class MondayItem(models.Model):
    """Class for storing Items received from Monday.com"""
    _name = "monday.item"
    _description = "Monday Item"
    _order = "board_id, id"

    board_id = fields.Many2one('monday.board', ondelete='cascade',
                               help="This indicates the board")
    group_id = fields.Many2one('monday.group', ondelete='set null',
                               domain="[('board_id', '=', board_id)]",
                               help="This indicates the group")
    item_reference = fields.Char(string="Item ID", index=True, readonly=True,
                                 help="It is the Monday.com id of the item")
    name = fields.Char(string="Item", help="It is the name of the item",
                       readonly=True)
    column_value_ids = fields.One2many('item.column.value',
                                       'item_id',
                                       help="It is the Column Value of the "
                                            "item")
