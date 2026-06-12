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

    rec_model = fields.Many2one('ir.model', string="Model",
                                help="Used to identify the source object of "
                                     "the export operation.")
    rec_id = fields.Char(string="Record ID", help="The unique database ID of "
                                                  "the exported record within "
                                                  "the selected model.")
    rec_name = fields.Char(string="Record Name", help="The display name of the"
                                                      " exported record")
    export_date = fields.Datetime(string="Export Date",
                                  default=lambda self: fields.Datetime.now(),
                                  help="The exact date and time when the export "
                                       "operation was performed. ")
    exported_fields_ids = fields.Many2many('ir.model.fields',
                                           string="Exported Fields",
                                           help="List of fields that were selected "
                                                "and exported for the record. ")
    export_user_id = fields.Many2one("res.users", string="Exported by",
                                     default=lambda self: self.env.user,
                                     help="The user who initiated or performed "
                                          "the export operation.")

    def action_create_export_log(self, vals):
        """
        To create export logs
        """
        for rec in vals['records']:
            rec_model_id = self.env['ir.model'].sudo().search(
                [('model', '=', rec['rec_model'])]
            ).id
            self.sudo().create({
                "rec_model": rec_model_id,
                "rec_id": rec['rec_id'],
                "rec_name": self.env[rec['rec_model']].sudo().search(
                    [('id', '=', rec['rec_id'])]
                ).name_get()[0][1],
                "exported_fields_ids": [
                    fields.Command.link(
                        self.env['ir.model.fields'].sudo().search([
                            ('model_id', '=', rec_model_id),
                            ('name', '=', i['field_name'])
                        ]).id
                    )
                    for i in vals['exportList']
                ],
            })
