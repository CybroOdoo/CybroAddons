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


class LinkedinComments(models.Model):
    """Class for retrieving comments of shared post."""
    _name = 'linkedin.comments'
    _description = 'LinkedIn Comments'

    post_id = fields.Many2one('hr.job', string="Job Post", ondelete='cascade',
                             help="Post ID of the particular job post")
    comments_id = fields.Char(string="Comments ID",
                              help="For specifying the comments ID")
    linkedin_comments = fields.Char(string="Comments",
                                    help="To add the posts comments")
