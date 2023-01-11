# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
'''Model For Creating Crop Requests'''
from odoo import models, fields, api, _


class CropRequests(models.Model):
    '''Details to create Crop Requests'''
    _name = 'crop.requests'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Agriculture Management"
    _rec_name = 'ref'

    ref = fields.Char(string='Reference', required=True, copy=False,
                      readonly=True, tracking=True,
                      default=lambda self: _('New'))
    farmer_id = fields.Many2one('farmer.details', string='Farmer',
                                required=True, tracking=True)
    seed_id = fields.Many2one('seed.details', string='Crop', required=True,
                              tracking=True)
    location_id = fields.Many2one('location.details', string='Location',
                                  required=True, tracking=True)
    request_date = fields.Date(string='Request Date',
                               default=fields.Date.context_today, required=True,
                               tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'),
         ('ploughing', 'Ploughing'), ('sowing', 'Sowing'),
         ('manuring', 'Manuring'), ('irrigation', 'Irrigation'),
         ('weeding', 'Weeding'), ('harvest', 'Harvest'), ('storage', 'Storage'),
         ('cancel', 'Cancel')],
        string='Status', default='draft', tracking=True,
        group_expand='_group_expand_states')
    note = fields.Text(string='Note', tracking=True)
    machinery_ids = fields.One2many('crop.machinery', 'des', string='Machinery',
                                    tracking=True)
    animal_ids = fields.One2many('crop.animals', 'dec', string='Animals',
                                 tracking=True)
    tags_id = fields.Many2many('agr.tag', string='Tags', tracking=True)
    user_id = fields.Many2one('res.users', string='Responsible User',
                              default=lambda self: self.env.user)

    @api.model
    def create(self, values):
        if values.get('ref', _('New')) == _('New'):
            values['ref'] = self.env['ir.sequence'].next_by_code(
                'crop.requests') or _('New')
        res = super(CropRequests, self).create(values)
        return res

    def action_draft(self):
        self.state = 'draft'

    def action_confirm(self):
        self.state = 'confirm'

    def action_ploughing(self):
        self.state = 'ploughing'

    def action_sowing(self):
        self.state = 'sowing'

    def action_manuring(self):
        self.state = 'manuring'

    def action_irrigation(self):
        self.state = 'irrigation'

    def action_weeding(self):
        self.state = 'weeding'

    def action_harvest(self):
        self.state = 'harvest'

    def action_cancel(self):
        self.state = 'cancel'

    def action_storage(self):
        self.state = 'storage'

    def _group_expand_states(self, states, domain, order):
        return [key for
                key, val in type(self).state.selection]


class CropMachinery(models.Model):
    '''Model For Attaching Vehicles'''
    _name = 'crop.machinery'

    des = fields.Many2one('crop.requests')
    vehicle_id = fields.Many2one('vehicle.details', string='Vehicle',
                                 tracking=True)
    qty = fields.Integer(string='Quantity')


class CropAnimals(models.Model):
    '''Model For Attaching Animals'''
    _name = 'crop.animals'

    dec = fields.Many2one('crop.requests')
    animal_id = fields.Many2one('animal.details', string='Animal',
                                domain=[('state', '=', 'available')],
                                tracking=True)
    qty = fields.Integer(string='Quantity')
