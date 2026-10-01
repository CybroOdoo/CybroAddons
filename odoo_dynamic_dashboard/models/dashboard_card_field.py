# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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


class DashboardCardField(models.Model):
    """Model to store fields selected for table cards."""
    _name = 'dashboard.card.field'
    _description = 'Dashboard Card Field'
    _order = 'sequence'
    _rec_name = 'field_label'

    sequence = fields.Integer(string='Sequence', default=10, help='Sequence order of the field.')
    field_id = fields.Many2one(
        'ir.model.fields',
        string='Field',
        required=True,
        ondelete='cascade',
        domain="[('model_id', '=', parent.model_id),('name', '!=', 'id'),('store', '=', True),('ttype', 'not in', ['binary', 'many2many', 'one2many'])]",
        help='The field to be displayed.'
    )
    card_id = fields.Many2one(
        'dashboard.card',
        string='Card',
        required=True,
        ondelete='cascade',
        help='The dashboard card this field belongs to.'
    )
    field_name = fields.Char(
        related='field_id.name',
        string='Field Name',
        help='Technical name of the field.'
    )
    field_label = fields.Char(
        related='field_id.field_description',
        string='Field Label',
        help='Label of the field.'
    )
    type = fields.Selection(
        related='field_id.ttype',
        string='Field Type',
        help='Type of the field.'
    )
