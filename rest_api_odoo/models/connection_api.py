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
"""Model definition for managing REST API connection permissions."""
from odoo import fields, models


class ConnectionApi(models.Model):
    """This class is used to configure REST API access permissions for models."""
    _name = 'connection.api'
    _description = 'Connection REST API'
    _rec_name = 'model_id'

    model_id = fields.Many2one('ir.model',
                               domain="[('transient', '=', False)]",
                               help="Select a model that can be accessed via "
                                    "REST API requests.")
    is_get = fields.Boolean(string='GET',
                            help="Select this to enable the GET method "
                                 "while sending requests.")
    is_post = fields.Boolean(string='POST',
                             help="Select this to enable the POST method "
                                  "while sending requests.")
    is_put = fields.Boolean(string='PUT',
                            help="Select this to enable the PUT method "
                                 "while sending requests.")
    is_delete = fields.Boolean(string='DELETE',
                               help="Select this to enable the DELETE method "
                                    "while sending requests.")
