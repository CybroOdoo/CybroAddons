# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class SquadMembersLine(models.Model):
    """Represents an individual line entry for a squad member call routing rule.
    Each line is associated with a specific language and assistant to
    whom the call will be transferred when a caller selects a language."""
    _name = "squad.members.line"
    _description = "Squad Members Line"
    _rec_name = "squad_id"

    assistant_id = fields.Many2one('ora.ai', string="Assistant",
                                   help="Assistant to whom the call will be "
                                        "routed when the language is "
                                        "selected.")
    transfer_modes = fields.Selection(string="Tranfer mode", selection=[
        ('swap-system-message-in-history', 'swap-system-message-in-history'),
        ('rolling-history', 'rolling-history')], required=True,
                                      default="swap-system-message-in-history",
                                      help="Mode of handling the conversation "
                                           "history during the transfer.")
    description = fields.Char(string="Description",
                              compute="_compute_description",
                              help="Auto-generated description based on the "
                                   "selected assistant and language.")
    message = fields.Char(string="Message",
                          default="please hold the line while transfer the "
                                  "call",
                          help="Message to be  displayed during the "
                               "call transfer process.")
    squad_id = fields.Many2one('vapi.squad', string="Request",
                               help="The squad request this member line is "
                                    "associated with.")
    language = fields.Char("Language", related="assistant_id.language_id.name",
                           help="Language selected by the caller,"
                                "derived from the assistant's language.")

    @api.depends('assistant_id')
    def _compute_description(self):
        """Automatically generate a description for the squad line entry
        based on the selected assistant's language and name."""
        for rec in self:
            rec.description = (f"when the caller choose the language "
                               f"{rec.assistant_id.language_id.name} ,transfer"
                               f" the call to assistant {rec.assistant_id.name}"
                               )
