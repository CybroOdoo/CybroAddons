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
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class TranscriberModel(models.Model):
    """speech-to-text model configurations used for transcribing voice input
    in the assistant system."""
    _name = "transcriber.model"
    _description = "Transcriber Model"

    name = fields.Char(string="Model Name", help="The display name of the transcription model (e.g., Nova-2, Whisper).")
    key = fields.Char(string="Model Key",
                      help="Unique key used to identify the model when"
                           " integrating with transcription APIs.")
    provider = fields.Char(
        help="The name of the service provider offering this"
             " transcription model (e.g., Deepgram, Gladia).")

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.is_superuser() and not self.env.context.get('install_mode'):
            raise UserError(self.env._("Transcriber Models cannot be created manually."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.is_superuser() and not self.env.context.get('install_mode'):
            raise UserError(self.env._("Transcriber Models cannot be edited."))
        return super().write(vals)
