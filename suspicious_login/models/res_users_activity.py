# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
#
#   This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
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


class ResUsersActivity(models.Model):
    """ Model for tracking user activities.This class defines a model named
    'res.users.activity' to track user activities. It stores information about
     user actions and is associated with the 'res.users' model."""
    _name = 'res.users.activity'
    _description = 'User activity'

    user_id = fields.Many2one('res.users', string='User',
                              help="Select the user associated with this"
                                   " record.")
    user_uid = fields.Char(string='User UID',
                           help="The unique identifier for the user.")
