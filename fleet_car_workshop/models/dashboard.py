# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2008-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.tools.translate import _
from openerp.osv import fields, osv


class CarVehicle(osv.osv):
    _name = 'car.car'
    _description = "Vechicles"
    _inherit = ['mail.thread']

    def _get_visibility_selection_id(self, cr, uid, context=None):
        """ Overriden in portal_project to offer more options """
        return [('portal', _('Customer Project: visible in portal if the customer is a follower')),
                ('employees', _('All Employees Project: all employees can access')),
                ('followers', _('Private Project: followers only'))]

    _visibility_selections = lambda self, *args, **kwargs: self._get_visibility_selection_id(*args, **kwargs)

    def get_task_count(self, cr, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        res = {}
        for vehicle in self.browse(cr, uid, ids, context=context):
            res[vehicle.id] = len(vehicle.task_ids)
        return res

    def _get_all_attached_docs(self, cr, uid, ids, field_name, arg, context):
        res = {}
        attachment = self.pool.get('ir.attachment')
        worksheet = self.pool.get('car.workshop')
        for id in ids:
            project_attachments = attachment.search(cr, uid, [('res_model', '=', 'car.car'),
                                                              ('res_id', '=', id)], context=context, count=True)
            task_ids = worksheet.search(cr, uid, [('vehicle_id', '=', id)], context=context)
            task_attachments = attachment.search(cr, uid, [('res_model', '=', 'car.workshop'),
                                                           ('res_id', 'in', task_ids)], context=context, count=True)
            res[id] = (project_attachments or 0) + (task_attachments or 0)
        return res

    def attachment_tree_views(self, cr, uid, ids, context):
        task_ids = self.pool.get('car.workshop').search(cr, uid, [('vehicle_id', 'in', ids)])
        domain = [
             '|',
             '&', ('res_model', '=', 'car.car'), ('res_id', 'in', ids),
             '&', ('res_model', '=', 'car.workshop'), ('res_id', 'in', task_ids)]
        res_id = ids and ids[0] or False
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Documents are attached to the tasks and issues of your project.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your project.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
        }

    _columns = {
        'active': fields.boolean('Active'),
        'name': fields.many2one('fleet.vehicle', string='Vehicle Name', track_visibility='onchange', required=True),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of Projects."),

        'label_tasks': fields.char(string='Use Tasks as', help="Gives label to tasks on project's kanban view."),
        'worksheet': fields.one2many('car.workshop', 'vehicle_id', string="Task Activities"),

        'type_ids': fields.many2many('worksheet.stages', 'car_workshop_type_rel',
                                     'vehicle_id', 'type_id', string='Worksheet Stages',
                                     states={'close': [('readonly', True)], 'cancelled': [('readonly', True)]}),
        'task_count': fields.function(get_task_count, type='integer', string="Tasks", ),
        'task_ids': fields.one2many('car.workshop', 'vehicle_id',
                                    domain=['|', ('stage_id.fold', '=', False), ('stage_id', '=', False)]),
        'doc_count': fields.function(_get_all_attached_docs, string="Number of documents attached", type='integer'),
        'color': fields.integer(string='Color Index'),
        'partner_id':  fields.many2one('res.partner', string='Customer'),
        'state': fields.selection([('draft', 'New'),
                                   ('open', 'In Progress'),
                                   ('cancelled', 'Cancelled'),
                                   ('pending', 'Pending'),
                                   ('close', 'Closed')], string='Status', required=True,
                                  track_visibility='onchange', copy=False),

        'date_start': fields.date(string='Start Date'),
        'date': fields.date(string='Expiration Date', select=True, track_visibility='onchange'),
        'use_tasks': fields.boolean(string='Tasks'),
        'image_medium': fields.related('name', 'image_medium', type="binary", string="Logo (medium)"),
        }

    _defaults = {
        'active': True,
        'use_tasks': True,
        'label_tasks': 'Tasks',
        'state': 'open',

    }

    def on_change_vehicle(self):
        if not self.name:
            return {}
        model = self.pool.get('fleet.vehicle').browse(self.name)
        return {
            'value': {
                'image_medium': model.image_medium,
            }
        }
