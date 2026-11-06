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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Helpers shared by every model that hides print buttons for a user.

The toolbar only holds the reports bound to the model (the entries of the
cog/three dots *Print* menu).  The buttons placed in the view itself - the
"Print" button of a transfer header, "Print Labels", the report buttons of a
purchase order - are plain ``<button>`` nodes of the arch, so they survive a
toolbar cleanup.  These helpers strip both.
"""
from lxml import etree

PRINT_KEYWORD = 'print'
SEND_KEYWORD = 'send'
LIST_TAGS = ('list', 'tree')


def hide_print_buttons(env, res):
    """Remove every print entry from the result of ``get_views``.

    env(odoo.api.Environment): environment of the calling model.
    res(dict): value returned by ``get_views``, updated in place.
    """
    for view in (res.get('views') or {}).values():
        toolbar = view.get('toolbar') or {}
        if toolbar.get('print'):
            toolbar['print'].clear()
        if view.get('arch'):
            view['arch'] = hide_arch_print_buttons(env, view['arch'])


def hide_arch_print_buttons(env, arch):
    """Return the arch with every print button made invisible.

    env(odoo.api.Environment): environment used to identify report actions.
    arch(str): view architecture returned by ``get_view``.
    str: the architecture, unchanged when it holds no print button.
    """
    root = etree.fromstring(arch)
    buttons = list(root.iter('button'))
    action_ids = [
        int(button.get('name'))
        for button in buttons
        if button.get('type') == 'action'
        and (button.get('name') or '').isdigit()
    ]
    report_ids = get_report_action_ids(env, action_ids)
    hidden = False
    for button in buttons:
        if not is_print_button(button, report_ids):
            continue
        button.set('invisible', '1')
        if root.tag in LIST_TAGS:
            button.set('column_invisible', '1')
        hidden = True
    if not hidden:
        return arch
    return etree.tostring(root, encoding='unicode')


def get_report_action_ids(env, action_ids):
    """Return the ids that are actually ``ir.actions.report`` records.

    env(odoo.api.Environment): environment used for the lookup.
    action_ids(list): action ids referenced by the buttons of a view.
    set: the subset of ids stored as reports.
    """
    if not action_ids:
        return set()
    return set(env['ir.actions.report'].sudo().browse(action_ids).exists().ids)


def is_print_button(button, report_ids):
    """Tell whether a button of the arch prints something.

    A button prints when it calls a report action, when its method name says
    so (``do_print_picking``, ``action_print_pdf``) or when its label does
    (``Print Labels``).  Buttons that send a document by mail are kept, as
    they are not print buttons.
    button(etree._Element): the ``<button>`` node of the arch.
    report_ids(set): ids of the report actions of the view.
    bool: True when the button has to be hidden.
    """
    name = (button.get('name') or '').lower()
    label = (button.get('string') or '').lower()
    if button.get('type') == 'action' and name.isdigit():
        if int(name) in report_ids:
            return True
    for value in (name, label):
        if PRINT_KEYWORD in value and SEND_KEYWORD not in value:
            return True
    return False
