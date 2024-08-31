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
from odoo import fields, models


class StickyNotesDelete(models.TransientModel):
    """This is ued to confirm the note to be deleted or not."""
    _name = 'sticky.notes.delete'
    _description = 'Sticky notes delete wizard'

    color = fields.Char(string='Color', default='Yellow',
                        help='Color of the note')
    note = fields.Text(string='Note', help='The note that we want to stick')
    active_model = fields.Integer(string='Id', help='The current record id')
    active_model_name = fields.Char(string='Active Model name',
                                    help='Current records model name')
    active_view = fields.Integer(string='Active View Id',
                                 help='Current records view id')

    def action_delete_notes(self):
        """This is used to delete the note"""
        record_view = self.env['ir.ui.view'].browse(
            self.env.context.get('view_id'))
        for rec in record_view.inherit_children_ids:
            stick_notes = rec.name.split('.')[0]
            if stick_notes.strip() == 'Sticky Notes':
                arch_note = rec.arch.split('<b ')[1].split('</b>')[0].split('>')[1]
                arch_heading = rec.arch.split('<i')[1].split('</i>')[0].split('>')[1]
                note_trim = self.note.replace(" ", "")
                heading_note = arch_heading+arch_note
                heading_note_trim = heading_note.replace(" ", "")
                if note_trim.strip() == heading_note_trim.strip():
                    stick_note_view = self.env['ir.ui.view'].browse(
                      self.env.context['view_id']).inherit_children_ids.filtered(
                        lambda l: l.name == rec.name.strip())
                    stick_note_view.unlink()
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
