# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class DeleteLog(models.Model):
    """Model to log information about deleted records"""
    _name = 'delete.log'
    _description = 'Delete Log'
    _rec_name = 'rec_name'

    rec_model = fields.Many2one('ir.model', string="Model", help="Model Name")
    rec_id = fields.Char(string="Record ID", help="ID of the record")
    rec_name = fields.Char(string="Record Name", help="Name of the record")
    delete_date = fields.Datetime(string="Delete Date",
                                  default=lambda self: fields.Datetime.now(),
                                  help="Delete date of the record")
    user_id = fields.Many2one("res.users", string="Deleted by",
                              default=lambda self: self.env.user,
                              help="User which this record is deleted by")


class BaseModel(models.AbstractModel):
    """Overrides the default unlink method to create record in DeleteLog
    model"""
    _inherit = 'base'

    def unlink(self):
        """Creates records inside delete.log model"""
        for rec_ids in self._cr.split_for_in_conditions(self.ids):
            records = self.browse(rec_ids)
            tracked_models = self.env['ir.config_parameter'].sudo().get_param(
                'export_delete_login_log.delete_log_models_ids')
            if tracked_models:
                if type(records)._name in [self.env['ir.model'].sudo().search(
                        [('id', '=', rec)]
                ).model for rec in eval(tracked_models)]:
                    self.env['delete.log'].sudo().create({
                        "rec_model": self.env['ir.model'].sudo().search(
                            [('model', '=', records._name)]).id,
                        "rec_id": records.id,
                        "rec_name": records.name_get()[0][1],
                    })
        return super().unlink()
