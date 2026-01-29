# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nandakishore M (odoo@cybrosys.info)
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
################################################################################
from odoo import fields, models


class VolunteerType(models.Model):
    """This class represents the different types of volunteers."""
    _name = "volunteer.type"
    _description = "Volunteer Type"
    _rec_name = 'volunteer_type'

    volunteer_type = fields.Char(String='Name', help='The name of the '
                                                     'volunteer type',
                                 required=True)
    volunteer_code = fields.Char(String='code', help='The code of the '
                                                     'volunteer type',
                                 required=True)
    description = fields.Html(String='Description', translate=True,
                              help='A description of the volunteer type')
