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
from odoo import http
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.http import request


class EasyLanguageSelector(http.Controller):
    """
    The EasyLanguageSelector class appending the activated languages in the
    systray language selection field.
        Methods:
            get_activated_languages(self):
                when the page is loaded adding total activated languages options
                 to the selection field.
                return a list variable.
            activated_languages(self, **kw):
                getting value of the selected language and change the language
                in the backend.
    """

    @http.route('/easy_language_selector/options', auth='user',
                type='jsonrpc')
    def get_activated_languages(self):
        """
        Summary:
            transferring data to the selection field that works as a language
            selector.
        Returns:
            type:list of lists , it contains the data for the language selector.
        """
        languages = request.env['res.lang'].search([('active', '=', True)])
        return [{'name': language.name, 'code': language.code}
                for language in languages]

    @http.route('/easy_language_selector/change', auth='user',
                type='jsonrpc')
    def change_active_languages(self, **kw):
        """
        Summary:
            getting value of the selected language and change the language in
            the backend.
        Args:
            kw(dict):it consists of the code of the selected language.
        """
        language_code = kw.get('code')
        language = request.env['res.lang'].search([
            ('code', '=', language_code),
            ('active', '=', True),
        ], limit=1)
        if not language:
            raise ValidationError(_('The selected language is not active.'))
        request.env.user.write({'lang': language.code})
        return True
