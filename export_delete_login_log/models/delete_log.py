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


class DeleteLog(models.Model):
    """Model to log information about deleted records"""
    _name = 'delete.log'
    _description = 'Delete Log'
    _rec_name = 'rec_name'

    rec_model = fields.Many2one('ir.model', string="Model",
                                help="Helps identify the type of record.")
    rec_id = fields.Char(string="Record ID", help="Used to identify which "
                                                  "specific record was deleted.")
    rec_name = fields.Char(string="Record Name", help="Typically corresponds to "
                                                      "the 'name' field or display "
                                                      "name in the UI.")
    delete_date = fields.Datetime(string="Delete Date",
                                  default=lambda self: fields.Datetime.now(),
                                  help="Timestamp indicating when the record was"
                                       " deleted. ")
    user_id = fields.Many2one("res.users", string="Deleted by",
                              default=lambda self: self.env.user,
                              help="The user account that performed the deletion.")
