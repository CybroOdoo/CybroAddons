# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP S (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models


class MobileComplaintTree(models.Model):
    _name = 'mobile.complaint.tree'
    _description = 'Mobile Complaint Tree'
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
