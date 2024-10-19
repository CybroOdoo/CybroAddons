# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class MobileComplaintDescription(models.Model):
    """This model represents description about the mobile Complaint"""
    _name = 'mobile.complaint.description'
    _description = "Mobile Complaint Description"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'description'

    complaint_type_template = fields.Many2one('mobile.complaint',
                                              string="Complaint Type",
                                              required=True,
                                              help="Complaint type template.")
    description = fields.Text(string="Description",
                              help="Complaint description.")
