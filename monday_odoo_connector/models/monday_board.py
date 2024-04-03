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


class MondayBoard(models.Model):
    """Class for storing Boards received from Monday.com"""
    _name = "monday.board"
    _description = "Monday Boards"

    name = fields.Char(string="Board", help="It is the name of the board")
    board_reference = fields.Char(string="Board ID",
                                  help="It is the reference number of the "
                                       "board")
    owner = fields.Char(string="Owner", help="It is the owner of the board")
    description = fields.Char(string="Description",
                              help="It is the detailed description of the "
                                   "board")
    group_ids = fields.One2many('monday.group',
                                'board_id', string="Group",
                                help="It indicates the Groups of Board")
    item_ids = fields.One2many('monday.item',
                               'board_id', string="Item",
                               help="It indicates the item of board")
