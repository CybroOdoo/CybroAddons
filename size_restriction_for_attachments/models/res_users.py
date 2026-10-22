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


class ResUsers(models.Model):
    """ Inherits res.users """
    _inherit = 'res.users'

    set_restriction = fields.Boolean(help="If true then that person "
                                          "will have restriction on "
                                          "size of the attachment to "
                                          "be uploaded.")
    max_size = fields.Float(string="Maximum Size (MB)", default=0.0,
                            help="Maximum size of attachment in MB.")
