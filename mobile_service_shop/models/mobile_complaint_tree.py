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


class MobileComplaintTree(models.Model):
    """Model for managing complaint details in mobile services."""
    _name = 'mobile.complaint.tree'
    _description = 'Mobile Complaint Tree'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'complaint_type_tree'

    complaint_id = fields.Many2one('mobile.service',
                                   string="Complaint ID",
                                   help="Complaint id associated with this "
                                        "record.")
    complaint_type_tree = fields.Many2one('mobile.complaint',
                                          string="Category",
                                          required=True,
                                          help="Complaint type tree records.")
    description_tree = fields.Many2one('mobile.complaint.description',
                                       string="Description",
                                       domain="[('complaint_type_template',"
                                              "'=',complaint_type_tree)]",
                                       help="Description field for the "
                                            "complaint.")
