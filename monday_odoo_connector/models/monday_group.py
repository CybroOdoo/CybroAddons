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


class MondayGroup(models.Model):
    """Class for storing Groups received from Monday.com"""
    _name = "monday.group"
    _description = "Monday Group"
    _order = "board_id, id"

    _board_group_uniq = models.Constraint(
        'unique(board_id, "group")',
        "The Monday.com group is already imported for this board.",
    )

    name = fields.Char(help="It is the name of the group", readonly=True)
    group = fields.Char(string='Group ID', help="It is the id of the group",
                        readonly=True)
    board_id = fields.Many2one('monday.board', ondelete='cascade',
                               help="It is the board of the group",
                               readonly=True)
