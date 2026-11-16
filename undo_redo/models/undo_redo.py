# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class UndoRedo(models.TransientModel):  # pylint: disable=no-wizard-in-models
    """Transient model to temporarily store undo and redo logs for
    record changes across all models."""
    _name = 'undo.redo'
    _description = 'Undo Redo'
    _transient_max_hours = 1
    _transient_max_count = 0

    table_name = fields.Char(required=True)
    record_id = fields.Integer(string="Record ID", required=True)
    updated_data = fields.Json()
    mode = fields.Selection([
        ('undo', 'Undo'),
        ('redo', 'Redo'),
    ])
    user_id = fields.Many2one("res.users")

    @api.model
    def get_data(self, table_name, record_id, mode="undo"):
        """Retrieve a list of undo/redo record IDs matching the given table
        name, record ID, and operation mode. Most recent record comes first.
        """
        if not table_name or not record_id:
            return []
        undo_record = self.env['undo.redo'].search(
            [
                ('table_name', '=', table_name.replace(".", "_")),
                ('record_id', '=', record_id),
                ('mode', '=', mode),
            ],
            order='id DESC',
        )
        return undo_record.ids

    def _register_hook(self):
        """Register hook to ensure PostgreSQL triggers are refreshed
        for newly created tables on registry loading."""
        super()._register_hook()
        try:
            with self.env.cr.savepoint():
                self.env.cr.execute("SELECT add_update_trigger_to_new_tables();")
        except Exception as e:
            _logger.warning("Could not execute trigger registration hook: %s", e)
