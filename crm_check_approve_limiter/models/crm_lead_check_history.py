# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
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
"""Module Containing CRM lead and CheckList History Models"""
from odoo import fields, models


class CrmLeadCheckHistory(models.Model):
    """class for to check the history of stage"""
    _name = "crm.lead.check.history"
    _description = "Model to track the history of stage changes for CRM leads"

    check_item_id = fields.Many2one('stage.check.list',
                                    string="Check Item",
                                    help="Many2one field representing the "
                                         "associated check item.")
    list_action = fields.Selection([('complete', 'Complete'),
                                    ('not_complete', 'Not Complete')],
                                   required=True, string="Action",
                                   help="Selection field representing "
                                        "the action for the check item.")
    user_id = fields.Many2one('res.users', string="User",
                              help="Many2one field representing the associated"
                                   " user.")
    change_date = fields.Datetime(string="Date",
                                  help="Datetime field representing the"
                                       " date of the check item action.")
    stage_id = fields.Many2one('crm.stage', string="Stage",
                               help="Many2one field representing "
                                    "the associated stage.")
    lead_id = fields.Many2one('crm.lead', string="Lead",
                              help="Many2one field representing the"
                                   " associated lead.")
