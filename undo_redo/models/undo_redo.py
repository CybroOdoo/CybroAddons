# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
from odoo import api, fields, models


class UndoRedo(models.TransientModel):
    """Transient model to temporarily store undo and redo logs for
    record changes across all models."""
    _name = 'undo.redo'
    _description = 'Undo Redo'
    _transient_max_hours = 1
    _transient_max_count = 0

    table_name = fields.Char(string="Name")
    record_id = fields.Integer(string="Record Id")
    updated_data = fields.Json("Updated Data")
    mode = fields.Selection([
        ('undo', 'Undo'),
        ('redo', 'Redo'),
    ], string="Mode")
    user_id = fields.Many2one("res.users")

    @api.model
    def get_data(self, table_name, record_id, mode="undo"):
        """Retrieve a list of undo/redo record IDs matching the given table
         name,record ID, and operation mode. Most recent record comes first.
         """
        undo_record = self.env['undo.redo'].search(
            [('table_name', '=', table_name.replace(".", "_")), ('record_id', '=', record_id), ('mode', '=', mode)],
            order='id DESC',
        )
        return undo_record.ids
