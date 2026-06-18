# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock

class TestTranslationWizard(TransactionCase):

    def setUp(self):
        super(TestTranslationWizard, self).setUp()
        self.lang_fr = self.env['res.lang'].with_context(active_test=False).search([('code', '=', 'fr_FR')], limit=1)
        if not self.lang_fr:
            self.lang_fr = self.env['res.lang'].create({
                'name': 'French',
                'code': 'fr_FR',
                'iso_code': 'fr',
                'url_code': 'fr',
                'active': True,
            })
            
        self.module = self.env['ir.module.module'].search([('name', '=', 'base'), ('state', '=', 'installed')], limit=1)
        
        self.wizard = self.env['automatic.translation.wizard'].create({
            'language_id': self.lang_fr.id,
            'module_id': self.module.id,
            'overwrite_existing_terms': False,
        })

    @patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.GoogleTranslator')
    @patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.trans_export')
    @patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.polib')
    def test_action_translate(self, mock_polib, mock_trans_export, mock_google_translator):
        """ Test the basic flow of the translation wizard with mocked external API """
        # Mock Google Translator
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Bonjour"
        mock_google_translator.return_value = mock_translator_instance

        # Mock trans_export to return True (success)
        mock_trans_export.return_value = True

        # Mock polib PO file and entries
        mock_po = MagicMock()
        mock_entry = MagicMock()
        mock_entry.msgid = "Hello"
        mock_entry.msgstr = ""
        mock_po.__iter__.return_value = [mock_entry]
        mock_polib.pofile.return_value = mock_po

        # Prevent actual save to filesystem during test
        with patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.os.path.exists', return_value=True), \
             patch('odoo.addons.automatic_module_translation.wizard.translation_wizard.get_module_path', return_value='/tmp/test_module'):
            
            # Execute the translation wizard
            result = self.wizard.action_translate()

            # Assertions
            # 1. trans_export was called
            self.assertTrue(mock_trans_export.called)
            
            # 2. polib parsed the content
            self.assertTrue(mock_polib.pofile.called)

            # 3. Assert that the client action reload is returned
            self.assertEqual(result.get('type'), 'ir.actions.client')
            self.assertEqual(result.get('tag'), 'reload')
