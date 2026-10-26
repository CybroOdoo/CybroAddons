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


class DonorType(models.Model):
    """This class represents the donor type model, which stores
    information related to different types of donors."""
    _name = "donor.type"
    _description = "Donor Type"
    _rec_name = 'donor_type'

    donor_type = fields.Char(string='Name', help='The name of the donor type',
                             required=True)
    donor_code = fields.Char(string='Donor Code', required=True,
                             help='The code of the donor code')
    description = fields.Html(string='Description', translate=True,
                              help='A description of the donor type')
