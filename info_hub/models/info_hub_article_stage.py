# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models

class InformationArticleStage(models.Model):
    """Kanban stage definition scoped to a single parent info article.

    Each stage belongs to one parent article and is used to organise article items
    in the embedded Kanban view. Default stages ('New', 'Ongoing', 'Done') are
    auto-created when the first item is added to an article.
    """

    _name = 'info.hub.article.stage'
    _description = 'Information Article Stage'
    _order = 'sequence, id'

    name = fields.Char(
        string='Stage Name',
        required=True,
        translate=True,
        help='Name of the kanban stage.',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Used to order stages in the kanban view.',
    )
    fold = fields.Boolean(
        string='Folded in Kanban',
        default=False,
        help='Defines if the stage is folded by default in the kanban view.',
    )
    parent_id = fields.Many2one(
        comodel_name='info.hub.article',
        string='Parent Article',
        ondelete='cascade',
        required=True,
        index=True,
        help='Parent article this kanban stage belongs to.',
    )
