# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import fields, models


class ExportLog(models.Model):
    """Model to log information about exported records"""
    _name = 'export.log'
    _description = "Export Log"
    _rec_name = 'rec_name'

    rec_model_id = fields.Many2one('ir.model', string="Model",
                                help="Name of the model from which records were exported")
    rec_id = fields.Char(string="Record ID", help="Unique identifier (ID) of the exported record")
    rec_name = fields.Char(string="Record Name", help="Display name of the exported record")
    export_date = fields.Datetime(string="Export Date",
                                  default=lambda self: fields.Datetime.now(),
                                  help="Date and time when the record was exported")
    exported_fields_ids = fields.Many2many('ir.model.fields',
                                           string="Exported Fields",
                                           help="List of fields that were included in the export operation")
    export_user_id = fields.Many2one("res.users", string="Exported by",
                                     default=lambda self: self.env.user,
                                     help="User who performed the export operation")

    def action_create_export_log(self, vals):
        """
        To create export logs
        """
        for rec in vals['records']:
            rec_model_id = self.env['ir.model'].sudo().search(
                [('model', '=', rec['rec_model'])]
            ).id
            self.sudo().create({
                "rec_model_id": rec_model_id,
                "rec_id": rec['rec_id'],
                "rec_name": self.env[rec['rec_model']].sudo().search(
                    [('id', '=', rec['rec_id'])]
                ).name,
                "exported_fields_ids": [
                    fields.Command.link(
                        self.env['ir.model.fields'].sudo().search([
                            ('model_id', '=', rec_model_id),
                            ('name', '=', export['field_name'])
                        ]).id
                    )
                    for export in vals['exportList']
                ],
            })
