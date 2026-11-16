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
from odoo import api, fields, models


class VideoStore(models.Model):
    """In this model you can store recorded data as a record and view it
    later"""
    _name = 'video.store'
    _description = 'Screen Record Video Storage'
    _rec_name = 'date'

    date = fields.Datetime(string='Date', default=fields.Datetime.now,
                           help="Date of screen capture")
    description = fields.Char(string='Description',
                              help='Add description for recording')
    video = fields.Char(string='Screen Record',
                        help="Recorded videos can be viewed here")

    @api.model
    def video_record(self, url):
        """function used to create a record when the screen record is
         stopped"""
        self.create({'description': '', 'video': url})
        return True
