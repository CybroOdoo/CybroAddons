# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
import json
from odoo import fields, models


class RollBackRecord(models.Model):
    """To keep History of edited records."""
    _name = 'rollback.record'
    _description = 'Record History'

    history = fields.Text(String='Record History',
                          help="The affected fields and "
                               "their values will be shown.")
    res_model = fields.Char(string='Model',
                            help="Shows which model is subject to editing?")
    record = fields.Integer(string='Record ID',
                            help="Shows the id of the record")
    user = fields.Char(string='Edited By', default=lambda self: self.env.user,
                       help="Technical field finding the person responsible "
                            "for the edit.")
    write_time = fields.Datetime(string='Time', default=fields.Datetime.now,
                                 help="Technical field shows the time at which"
                                      "the record was edited.")

    def action_record_selection(self):
        """Selected record will update the current record"""
        json_load = json.loads(self.history)
        self.env[self.res_model].browse(self.record).sudo().write(
            {keys: json_load[keys] for keys in json_load.keys()})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    def get_models(self):
        """To get the model added in the settings"""
        many2many_field_ids = self.env['res.config.settings'].create({

        }).res_rollback_model_ids.ids
        return [x.model for x in self.env['ir.model'].browse(
            many2many_field_ids)]
