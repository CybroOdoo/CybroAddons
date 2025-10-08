"""Sticky notes"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from uuid import uuid4
from odoo import exceptions, fields, models, _


class StickyNotes(models.TransientModel):
    """Used to create sticky notes"""
    _name = 'sticky.notes'
    _description = 'Sticky notes'

    color = fields.Char(string='Color', default='Yellow',
                        help="Background color of the sticky note", size=7)
    note = fields.Text(string='Note', help='Text of the sticky note')
    active_model = fields.Integer(string='Id', help='Id of the active model')
    active_model_name = fields.Char(string='Active Model name',
                                    help='Name of active model for the '
                                         'current record')
    active_view = fields.Integer(string='Active View Id',
                                 help='View id of the record')
    text_color = fields.Char(string='Text Color', default='White',
                             help="Text color of the sticky notes", size=7)
    heading = fields.Char(string='Heading', required=True, help='Heading of '
                                                                'the note')

    def action_stick_notes(self):
        """This method is used to create sticky notes"""
        if not self.note:
            raise exceptions.ValidationError(_("Enter the note."))
        else:
            self.env['stick.notes'].create({
                'notes': self.note,
            })
            views = self.env['ir.ui.view'].browse(self.env.context['default_active_view'])
            for rec in views.inherit_children_ids:
                name = rec.name.split('.')[0]
                if name.strip() == 'Sticky Notes':
                    arch = ("""<xpath expr="//div[hasclass('sticky_notes_edit_delete')]"  position="inside">
                              <div draggable="true"
                                  role="alert" style="height:126px;width:200px;background-color:%s;text-color:%s;"
                                  class="card js_sticky_notes alert col-2" id="%s" attrs="{'invisible':[('id',
                                  '!=',%s)]}"><div  class="sticky_buttons" style="display:flex;justify-content:flex-end;"> 
                                  <button name="edit_notes"
                                  class="fa fa-pencil js_edit_notes"></button><button
                                  name="delete_notes" class="btn-btn-primary fa fa-trash
                                  js_note_delete"></button></div><div>
                                  <h3 style="color:%s"> <i> %s </i> </h3></div>
                                  <div><b style="color:%s"> %s </b></div></div>
                                  </xpath>""" % (
                        self.color, self.text_color,
                        str(self.active_model) + str(uuid4())[7:-18],
                        self.active_model, self.text_color, self.heading,
                        self.text_color,
                        self.note))
                    view_data = {
                        'name': "Sticky Notes .{}".format(str(self.id)),
                        'type': 'kanban',
                        'model': self.active_model_name,
                        'priority': 1,
                        'inherit_id': views.id,
                        'mode': 'extension',
                        'sticky_identification_number': str(self.id),
                        'arch_base': arch.encode('utf-8')
                    }
                    self.env["ir.ui.view"].create(view_data)
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                else:
                    base_arch = ("""<xpath expr="//form/sheet"  position="before"> 
                            <div
                            class="sticky_notes_edit_delete o_form_sheet"
                            style="display: flex;gap: 10px;padding: 0;background: none;border: none;box-shadow: none;"/>
                                </xpath> """)
                    view_data = {
                        'name': "",
                        'type': 'kanban',
                        'model': self.active_model_name,
                        'priority': 1,
                        'inherit_id': views.id,
                        'mode': 'extension',
                        'sticky_identification_number': str(self.id),
                        'arch_base': base_arch.encode('utf-8')
                    }
            self.env["ir.ui.view"].create(view_data)
            arch = ("""<xpath expr="//div[hasclass('sticky_notes_edit_delete')]"
                       position="inside">
                       <div draggable="true"
                           role="alert" style="height:126px;width:200px;
                           background-color:%s;text-color:%s;"
                           class="card js_sticky_notes alert col-2" id="%s" 
                           attrs="{'invisible':[('id',
                           '!=',%s)]}"><div  class="sticky_buttons" style="display:flex;justify-content:flex-end;"> <button 
                           name="edit_notes"
                           class="fa fa-pencil js_edit_notes"></button><button
                           name="delete_notes" class="btn-btn-primary fa fa-trash
                           js_note_delete"></button></div><div>
                           <h3 style="color:%s"> <i> %s </i> </h3></div>
                           <div><b style="color:%s"> %s </b></div></div>
                           </xpath>""" % (
                self.color, self.text_color,
                str(self.active_model) + str(uuid4())[7:-18],
                self.active_model, self.text_color, self.heading,
                self.text_color,
                self.note))
            view_data = {
                'name': "Sticky Notes .{}".format(str(self.id)),
                'type': 'kanban',
                'model': self.active_model_name,
                'priority': 1,
                'inherit_id': views.id,
                'mode': 'extension',
                'sticky_identification_number': str(self.id),
                'arch_base': arch.encode('utf-8')
            }
            self.env["ir.ui.view"].create(view_data)
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
