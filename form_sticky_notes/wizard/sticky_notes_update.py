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
from odoo import fields, models


class StickyNotesUpdate(models.TransientModel):
    """This is used to update the sticky notes"""
    _name = 'sticky.notes.update'
    _description = 'Sticky notes update wizard'

    background_color = fields.Char(string='Background Color',
                                   help="Color of notes")
    text_color = fields.Char(string='Text Color',
                             help="Color of Text")

    note = fields.Text(string='Note', help="Text for the sticky note",
                       required=True)
    heading = fields.Text(string='Heading', help="Heading of the sticky notes",
                          required=True)
    active_model = fields.Integer(string='Id', help="The active model id")
    active_model_name = fields.Char(string='Active Model name',
                                    help="Active model name of the note")
    active_view = fields.Integer(string='Active View Id',
                                 help="Active view id of the note")
    prev_heading = fields.Text(string='Prev Heading', help="previous heading "
                                                           "of the sticky note")
    prev_notes = fields.Text(string='Prev notes', help="Previous notes of "
                                                       "sticky note")

    def action_update_notes(self):
        """This is used to update the edited text to the sticky notes"""
        record_view = self.env['ir.ui.view'].browse(
            self.env.context.get('view_id'))
        for rec in record_view.inherit_children_ids:
            stick_notes = rec.name.split('.')[0]
            if stick_notes.strip() == 'Sticky Notes':
                arch_note = \
                    rec.arch.split('<b ')[1].split('</b>')[0].split('>')[1]
                arch_heading = \
                    rec.arch.split('<i')[1].split('</i>')[0].split('>')[1]
                current_record = (self.prev_heading + self.prev_notes).replace(
                    " ", "")
                rec_record = (arch_heading + arch_note).replace(" ", "")
                if current_record == rec_record:
                    rec.unlink()
                    views = self.env['ir.ui.view'].browse(
                        self.env.context['view_id'])
                    arch = ("""<xpath expr="//div[hasclass('sticky_notes_edit_delete')]" position="inside">
                              <div draggable="true"
                                  role="alert" style="height:126px;width:200px;background-color:%s;text-color:%s;"
                                  class="card js_sticky_notes alert col-2" id="%s" attrs="{'invisible':[('id',
                                  '!=',%s)]}"><div  class="sticky_buttons" style="display:flex;justify-content:flex-end;"> <button name="edit_notes"
                                  class="fa fa-pencil js_edit_notes"></button><button
                                  name="delete_notes" class="btn-btn-primary fa fa-trash
                                  js_note_delete"></button></div><div>
                                  <h3 style="color:%s"> <i> %s </i> </h3></div>
                                  <div><b style="color:%s"> %s </b></div></div>
                                  </xpath>""" % (
                        self.background_color, self.text_color,
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
