# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from unittest.mock import patch, MagicMock
import io
import os

class TestAutomaticTranslationWizard(TransactionCase):

    def setUp(self):
        super(TestAutomaticTranslationWizard, self).setUp()
        self.TranslationWizard = self.env['automatic.translation.wizard']
        
        # We need an installed module and a language.
        # Use 'base' as the installed module to ensure it's there.
        self.module_base = self.env['ir.module.module'].search([('name', '=', 'base'), ('state', '=', 'installed')], limit=1)
        
        # Ensure a language is installed to translate to. e.g., French
        self.lang_fr = self.env['res.lang'].with_context(active_test=False).search([('code', '=', 'fr_FR')], limit=1)
        if not self.lang_fr:
            self.lang_fr = self.env['res.lang'].create({
                'name': 'French',
                'code': 'fr_FR',
                'iso_code': 'fr',
                'url_code': 'fr',
                'active': True,
            })
        else:
            self.lang_fr.active = True

    @patch('odoo.modules.registry.Registry.signal_changes', MagicMock())
    @patch('odoo.modules.registry.Registry.clear_cache', MagicMock())
    @patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.polib')
    @patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.GoogleTranslator')
    @patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.trans_export')
    def test_action_translate_success(self, mock_trans_export, MockGoogleTranslator, mock_polib):
        """Test action_translate executes successfully with mocked dependencies"""
        
        wizard = self.TranslationWizard.create({
            'language_id': self.lang_fr.id,
            'module_id': self.module_base.id,
            'overwrite_existing_terms': False,
        })
        
        # Mock GoogleTranslator
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Bonjour"
        MockGoogleTranslator.return_value = mock_translator_instance
        
        # Mock trans_export
        def side_effect_trans_export(lang_code, modules, buf, ext, cr):
            buf.write(b'msgid "Hello"\nmsgstr ""\n')
        mock_trans_export.side_effect = side_effect_trans_export
        
        # Mock polib
        mock_entry = MagicMock()
        mock_entry.msgid = "Hello"
        mock_entry.msgstr = ""
        
        mock_po_file = MagicMock()
        mock_po_file.__iter__.return_value = [mock_entry]
        mock_polib.pofile.return_value = mock_po_file
        
        # Actually, we should mock get_module_path to avoid creating real directories during test
        with patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.get_module_path') as mock_get_module_path, \
             patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=False):
            
            mock_get_module_path.return_value = '/tmp/mock_odoo_module'
            
            # Run the method
            result = wizard.action_translate()
            
            # Assertions
            mock_trans_export.assert_called_once()
            mock_polib.pofile.assert_called_once()
            
            # The translated text should have been assigned to msgstr
            self.assertEqual(mock_entry.msgstr, "Bonjour")
            
            # Should have attempted to save the PO file
            mock_po_file.save.assert_called_once_with(os.path.join('/tmp/mock_odoo_module', 'i18n', 'fr_FR.po'))
            
            # It should return a client action to reload
            self.assertEqual(result.get('type'), 'ir.actions.client')
            self.assertEqual(result.get('tag'), 'reload')

    @patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.GoogleTranslator', new=None)
    def test_missing_google_translator(self):
        """Test that UserError is raised if GoogleTranslator is missing"""
        wizard = self.TranslationWizard.create({
            'language_id': self.lang_fr.id,
            'module_id': self.module_base.id,
        })
        
        with self.assertRaisesRegex(UserError, "Please install 'deep_translator'"):
            wizard.action_translate()

    @patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.polib', new=None)
    def test_missing_polib(self):
        """Test that UserError is raised if polib is missing"""
        wizard = self.TranslationWizard.create({
            'language_id': self.lang_fr.id,
            'module_id': self.module_base.id,
        })
        
        with self.assertRaisesRegex(UserError, "Please install 'polib'"):
            wizard.action_translate()
