# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swetha Anand (odoo@cybrosys.com)
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


class ResUSer(models.Model):
    """Inherits res.users. to add new fields to set restriction on size of the
    attachment to be uploaded and to set maximum size of attachment."""
    _inherit = 'res.users'

    set_restriction = fields.Boolean(string="Set Restriction",
                                     help="If true then that person "
                                          "will have restriction on "
                                          "size of the attachment to "
                                          "be uploaded.")
    max_size = fields.Float(string="Maximum size(MB)", default=0.0,
                            help="Maximum size of attachment in MB.")
