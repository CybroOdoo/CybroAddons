# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: ASWATHI C (<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
import base64

from odoo.osv import osv
from odoo.tools.translate import _
from odoo import fields, api


class CarVehicle(osv.osv):
    _name = 'car.car'
    _description = "Vechicles"
    _inherit = ['mail.thread']
    _rec_name = 'vehicle_id'

    active = fields.Boolean('Active', default=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle Name', tracking=True, required=True)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")

    label_tasks = fields.Char(string='Use Tasks as', help="Gives label to Work on kanban view.", default="Task")
    worksheet = fields.One2many('car.workshop', 'vehicle_id', string="Task Activities")

    type_ids = fields.Many2many('worksheet.stages', 'car_workshop_type_rel',
                                'vehicle_id', 'type_id', string='Worksheet Stages',
                                states={'close': [('readonly', True)], 'cancelled': [('readonly', True)]})

    task_count = fields.Integer(compute='_compute_task_count', type='integer', string="Tasks")
    task_ids = fields.One2many('car.workshop', 'vehicle_id',
                               domain=['|', ('stage_id.fold', '=', False), ('stage_id', '=', False)])
    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Number of documents attached")
    color = fields.Integer(string='Color Index')
    partner_id = fields.Many2one('res.partner', string='Customer')
    state = fields.Selection([('draft', 'New'),
                              ('open', 'In Progress'),
                              ('cancelled', 'Cancelled'),
                              ('pending', 'Pending'),
                              ('close', 'Closed')], string='Status', required=True,
                             track_visibility='onchange', default='open', copy=False)

    date_start = fields.Date(string='Start Date')
    date = fields.Date(string='Expiration Date', select=True, track_visibility='onchange')
    use_tasks = fields.Boolean(string='Tasks', default=True)
    image_128 = fields.Image(related='vehicle_id.image_128', readonly=False)

    def _get_visibility_selection_id(self, cr, uid, context=None):
        return [('portal', _('Customer Works: visible in portal if the customer is a follower')),
                ('employees', _('All Employees Work: all employees can access')),
                ('followers', _('Private Work: followers only'))]

    _visibility_selections = lambda self, *args, **kwargs: self._get_visibility_selection_id(*args, **kwargs)

    def _compute_attached_docs_count(self):
        Attachment = self.env['ir.attachment']
        for vehicle in self:
            vehicle.doc_count = Attachment.search_count([
                '|',
                '&',
                ('res_model', '=', 'car.car'), ('res_id', '=', vehicle.id),
                '&',
                ('res_model', '=', 'car.worksheet'), ('res_id', 'in', vehicle.task_ids.ids)
            ])

    def _compute_task_count(self):
        for vehicle in self:
            vehicle.task_count = len(vehicle.task_ids)

    def attachment_tree_views(self):
        self.ensure_one()
        domain = [
            '|',
            '&', ('res_model', '=', 'car.car'), ('res_id', 'in', self.ids),
            '&', ('res_model', '=', 'car.workshop'), ('res_id', 'in', self.task_ids.ids)]

        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Documents are attached to the tasks and issues of your Worksheet.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your Worksheet.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }
