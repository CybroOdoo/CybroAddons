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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class MailerCloudList(models.Model):
    """ Model representing a list in the Mailercloud."""
    _name = 'mailer.cloud.list'
    _description = 'Mailercloud List'

    mailer_cloud = fields.Char(
        string='Mailercloud ID',
        help='Unique identifier for the Mailercloud associated '
             'with this record.')
    name = fields.Char(
        help='Name or title associated with this record.')
    authorization_id = fields.Many2one(
        'mailer.cloud.api.sync',
        help='Reference to the Mailercloud API synchronization '
             'associated with this record.')
