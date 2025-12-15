# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class TranscriberModel(models.Model):
    """speech-to-text model configurations used for transcribing voice input
    in the assistant system."""
    _name = "transcriber.model"
    _description = "Transcriber Model"

    name = fields.Char(string="Model Name", help="The display name .")
    key = fields.Char(string="Model Key",
                      help="Unique key used to identify the model when"
                           " integrating with transcription APIs.")
    provider = fields.Char(
        string="Provider",
        help="The name of the service provider offering this"
             " transcription model (e.g., Deepgram, Gladia).")
