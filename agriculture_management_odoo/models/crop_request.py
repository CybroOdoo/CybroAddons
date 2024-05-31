# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _


class CropRequest(models.Model):
    """ This model represents the creation of crop requests. It provides a
    structured way to initiate and manage requests for crop cultivation tasks,
    including associating animals, machinery, and other relevant details."""
    _name = 'crop.request'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Crop Request Details"
    _rec_name = 'ref'

    ref = fields.Char(string='Reference', help="Reference id of crop requests",
                      copy=False, readonly=True, tracking=True,
                      default=lambda self: _('New'))
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, help='The company associated with the current user or '
        'environment.', default=lambda self: self.env.company)
    farmer_id = fields.Many2one('farmer.detail', string='Farmer',
                                help="Choose the farmer for the crop",
                                required=True, tracking=True)
    seed_id = fields.Many2one('seed.detail', string='Crop',
                              help=" Select the seed details",
                              required=True, tracking=True)
    location_id = fields.Many2one('location.detail',
                                  string='Location', required=True,
                                  help="Mention the Location details for "
                                       "farming", tracking=True)
    request_date = fields.Date(string='Request Date', tracking=True,
                               help="The Requested Date for crop",
                               default=fields.Date.context_today, required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'),
         ('ploughing', 'Ploughing'), ('sowing', 'Sowing'),
         ('manuring', 'Manuring'), ('irrigation', 'Irrigation'),
         ('weeding', 'Weeding'), ('harvest', 'Harvest'), ('storage', 'Storage'),
         ('cancel', 'Cancel')], group_expand='_group_expand_states',
        string='Status', default='draft', tracking=True,
        help="Mention the Status of crop, which stage now the crop is reached")
    note = fields.Text(string='Note', tracking=True,
                       help="Description about crop and farming need to "
                            "remember")
    machinery_ids = fields.One2many('crop.machinery',
                                    'des_id', string='Machinery',
                                    tracking=True, help="The machinery required"
                                                        "for this farming")
    animal_ids = fields.One2many('crop.animal',
                                 'dec_id', string='Animals',
                                 tracking=True,
                                 help="Animals used for this crop farming")
    tag_ids = fields.Many2many('agriculture.tag', string='Tags',
                               tracking=True, help="Create appropriate"
                                                   " tags for the crop ")
    user_id = fields.Many2one('res.users',
                              string='Responsible User',
                              help="Mention the user of the documents",
                              default=lambda self: self.env.user)

    @api.model
    def create(self, values):
        """Function for creating new crop requests"""
        if values.get('ref', _('New')) == _('New'):
            values['ref'] = self.env['ir.sequence'].next_by_code(
                'crop.request') or _('New')
        res = super(CropRequest, self).create(values)
        return res

    def action_draft(self):
        """ Function for change state of crop request to draft """
        self.state = 'draft'

    def action_confirm(self):
        """ Function for change state of crop request to confirm """
        self.state = 'confirm'

    def action_ploughing(self):
        """ Function for change state of crop request to ploughing """
        self.state = 'ploughing'

    def action_sowing(self):
        """ Function for change state of crop request to sowing """
        self.state = 'sowing'

    def action_manuring(self):
        """ Function for change state of crop request to manuring """
        self.state = 'manuring'

    def action_irrigation(self):
        """ Function for change state of crop request to irrigation """
        self.state = 'irrigation'

    def action_weeding(self):
        """ Function for change state of crop request to weeding """
        self.state = 'weeding'

    def action_harvest(self):
        """ Function for change state of crop request to harvest """
        self.state = 'harvest'

    def action_cancel(self):
        """ Function for change state of crop request to cancel """
        self.state = 'cancel'

    def action_storage(self):
        """ Function for change state of crop request to storage """
        self.state = 'storage'

    def _group_expand_states(self,states, domain, order):
        """This function takes a list of states and expands them based on the
        given domain and order."""
        return [key for
                key, val in type(self).state.selection]
