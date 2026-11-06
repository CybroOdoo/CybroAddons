# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

WIZARD_PKG = 'odoo.addons.automatic_module_translation.wizard.translation_wizard'


class TestTranslationWizard(TransactionCase):
    """
    Test suite for the Automatic Translation Wizard.
    Ensures that the wizard correctly handles the translation process,
    interacts with external APIs (mocked), and updates translation files.
    """

    def setUp(self):
        """
        Initialize test environment:
        - Ensure target language (French) exists.
        - Identify installed module (base).
        - Create an instance of the translation wizard.
        """
        super().setUp()
        self.lang_fr = self.env['res.lang'].with_context(active_test=False).search(
            [('code', '=', 'fr_FR')], limit=1
        )
        if not self.lang_fr:
            self.lang_fr = self.env['res.lang'].create({
                'name': 'French',
                'code': 'fr_FR',
                'iso_code': 'fr',
                'url_code': 'fr',
                'active': True,
            })

        self.module = self.env['ir.module.module'].search(
            [('name', '=', 'base'), ('state', '=', 'installed')], limit=1
        )

        self.wizard = self.env['automatic.translation.wizard'].create({
            'language_id': self.lang_fr.id,
            'module_id': self.module.id,
            'overwrite_existing_terms': False,
        })

    def _create_mock_po(self, entries):
        """Helper to create a mock PO object from list of (msgid, msgstr) tuples."""
        mock_po = MagicMock()
        mock_entries = []
        for msgid, msgstr in entries:
            mock_entry = MagicMock()
            mock_entry.msgid = msgid
            mock_entry.msgstr = msgstr
            mock_entries.append(mock_entry)
        mock_po.__iter__.return_value = mock_entries
        return mock_po

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=True)
    @patch(f'{WIZARD_PKG}.polib')
    def test_action_translate_success(self, mock_polib, _mock_trans_export, mock_google_translator):
        """Test the standard successful translation action of the wizard."""
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Bonjour"
        mock_google_translator.return_value = mock_translator_instance

        mock_po = self._create_mock_po([("Hello", "")])
        mock_polib.pofile.return_value = mock_po

        with patch(f'{WIZARD_PKG}.os.path.exists', return_value=True), \
             patch(f'{WIZARD_PKG}.get_module_path', return_value='/tmp/test_module'):

            result = self.wizard.action_translate()

            self.assertEqual(result.get('type'), 'ir.actions.client')
            self.assertEqual(result.get('tag'), 'reload')
            self.assertEqual(mock_po.__iter__.return_value[0].msgstr, "Bonjour")

    def test_action_translate_missing_google_translator(self):
        """Test UserError is raised when GoogleTranslator dependency is missing."""
        with patch(f'{WIZARD_PKG}.GoogleTranslator', None):
            with self.assertRaises(UserError) as err:
                self.wizard.action_translate()
            self.assertIn("deep_translator", str(err.exception))

    def test_action_translate_missing_polib(self):
        """Test UserError is raised when polib dependency is missing."""
        with patch(f'{WIZARD_PKG}.polib', None):
            with self.assertRaises(UserError) as err:
                self.wizard.action_translate()
            self.assertIn("polib", str(err.exception))

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    def test_action_translate_invalid_language_code(self, mock_google_translator):
        """Test UserError is raised when language code is invalid."""
        mock_google_translator.side_effect = Exception("Unsupported language")
        with self.assertRaises(UserError) as err:
            self.wizard.action_translate()
        self.assertIn("Invalid language code", str(err.exception))

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=False)
    def test_action_translate_no_terms_found(self, _mock_trans_export, _mock_google_translator):
        """Test UserError is raised when trans_export returns no translatable terms."""
        with self.assertRaises(UserError) as err:
            self.wizard.action_translate()
        self.assertIn("No translatable terms found", str(err.exception))

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', side_effect=Exception("Export error"))
    def test_action_translate_export_failure(self, _mock_trans_export, _mock_google_translator):
        """Test UserError is raised when trans_export encounters an unexpected failure."""
        with self.assertRaises(UserError) as err:
            self.wizard.action_translate()
        self.assertIn("Failed to export module translations", str(err.exception))

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=True)
    @patch(f'{WIZARD_PKG}.polib')
    def test_action_translate_po_parse_failure(self, mock_polib, _mock_trans_export, _mock_gt):
        """Test UserError is raised when polib fails to parse the exported PO content."""
        mock_polib.pofile.side_effect = Exception("Parse syntax error")
        with self.assertRaises(UserError) as err:
            self.wizard.action_translate()
        self.assertIn("Failed to parse PO content", str(err.exception))

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=True)
    @patch(f'{WIZARD_PKG}.polib')
    @patch(f'{WIZARD_PKG}.get_module_path', return_value=None)
    def test_action_translate_module_path_not_found(self, _mock_path, mock_polib, _mock_exp, _gt):
        """Test UserError is raised when get_module_path returns None."""
        mock_polib.pofile.return_value = self._create_mock_po([("Hello", "")])
        with self.assertRaises(UserError) as err:
            self.wizard.action_translate()
        self.assertIn("Module path not found", str(err.exception))

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=True)
    @patch(f'{WIZARD_PKG}.polib')
    @patch(f'{WIZARD_PKG}.get_module_path', return_value='/tmp/test_module')
    def test_action_translate_no_new_terms(self, _mock_path, mock_polib, _mock_exp, _mock_gt):
        """Test notification is returned when all terms already have translations."""
        mock_po = self._create_mock_po([("Hello", "Bonjour")])
        mock_polib.pofile.return_value = mock_po

        with patch(f'{WIZARD_PKG}.os.path.exists', return_value=True):
            result = self.wizard.action_translate()

        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'display_notification')
        self.assertIn("No new terms to translate", result.get('params', {}).get('message', ''))

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=True)
    @patch(f'{WIZARD_PKG}.polib')
    @patch(f'{WIZARD_PKG}.get_module_path', return_value='/tmp/test_module')
    def test_action_translate_load_disk_translations(self, _mock_path, mock_polib,
                                                     _mock_exp, mock_gt):
        """Test disk translations are preserved for untranslated terms when not overwriting."""
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Monde"
        mock_gt.return_value = mock_translator_instance

        # Exported PO has empty msgstr for both
        po_entry1 = MagicMock(msgid="Hello", msgstr="")
        po_entry2 = MagicMock(msgid="World", msgstr="")
        mock_exported_po = MagicMock()
        mock_exported_po.__iter__.return_value = [po_entry1, po_entry2]

        # Disk PO has existing translation for "Hello"
        disk_entry = MagicMock(msgid="Hello", msgstr="Bonjour")
        mock_disk_po = MagicMock()
        mock_disk_po.__iter__.return_value = [disk_entry]

        # polib.pofile called twice: first for export, second for disk PO
        mock_polib.pofile.side_effect = [mock_exported_po, mock_disk_po]

        with patch(f'{WIZARD_PKG}.os.path.exists', return_value=True):
            result = self.wizard.action_translate()

        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'reload')
        self.assertEqual(po_entry1.msgstr, "Bonjour")
        self.assertEqual(po_entry2.msgstr, "Monde")

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=True)
    @patch(f'{WIZARD_PKG}.polib')
    @patch(f'{WIZARD_PKG}.get_module_path', return_value='/tmp/test_module')
    def test_action_translate_overwrite_existing(self, _mock_path, mock_polib, _mock_exp, mock_gt):
        """Test terms are translated and overwritten when overwrite_existing_terms=True."""
        self.wizard.overwrite_existing_terms = True

        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Salut"
        mock_gt.return_value = mock_translator_instance

        mock_po = self._create_mock_po([("Hello", "Bonjour")])
        mock_polib.pofile.return_value = mock_po

        with patch(f'{WIZARD_PKG}.os.path.exists', return_value=True):
            result = self.wizard.action_translate()

        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'reload')

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=True)
    @patch(f'{WIZARD_PKG}.polib')
    @patch(f'{WIZARD_PKG}.requests.Session')
    @patch(f'{WIZARD_PKG}.get_module_path', return_value='/tmp/test_module')
    def test_action_translate_fallback_mymemory(self, _mock_path, mock_session_cls,
                                                 mock_polib, _mock_exp, mock_gt):
        """Test fallback translation to MyMemory service when GoogleTranslator fails."""
        mock_gt_instance = MagicMock()
        mock_gt_instance.translate.side_effect = Exception("Google rate limit")
        mock_gt.return_value = mock_gt_instance

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'responseStatus': 200,
            'responseData': {'translatedText': 'Bonjour le monde'}
        }
        mock_session_inst = MagicMock()
        mock_session_inst.get.return_value = mock_response
        mock_session_cls.return_value = mock_session_inst

        mock_po = self._create_mock_po([("Hello world", "")])
        mock_polib.pofile.return_value = mock_po

        with patch(f'{WIZARD_PKG}.os.path.exists', return_value=True):
            result = self.wizard.action_translate()

        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'reload')

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=True)
    @patch(f'{WIZARD_PKG}.polib')
    @patch(f'{WIZARD_PKG}.requests.Session')
    @patch(f'{WIZARD_PKG}.get_module_path', return_value='/tmp/test_module')
    def test_action_translate_all_services_fail(self, _mock_path, mock_session_cls,
                                                mock_polib, _mock_exp, mock_gt):
        """Test UserError is raised when all translation services fail to translate terms."""
        mock_gt_instance = MagicMock()
        mock_gt_instance.translate.side_effect = Exception("Connection error")
        mock_gt.return_value = mock_gt_instance

        mock_session_inst = MagicMock()
        mock_session_inst.get.side_effect = Exception("Network unreachable")
        mock_session_cls.return_value = mock_session_inst

        mock_po = self._create_mock_po([("Translate me", "")])
        mock_polib.pofile.return_value = mock_po

        with patch(f'{WIZARD_PKG}.os.path.exists', return_value=True):
            with self.assertRaises(UserError) as err:
                self.wizard.action_translate()
            self.assertIn("Translation failed", str(err.exception))

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=True)
    @patch(f'{WIZARD_PKG}.polib')
    @patch(f'{WIZARD_PKG}.os.makedirs', side_effect=PermissionError("Permission denied"))
    @patch(f'{WIZARD_PKG}.get_module_path', return_value='/tmp/test_module')
    def test_action_translate_mkdir_permission_error(self, _mock_path, _mock_mkdir,
                                                     mock_polib, _mock_exp, mock_gt):
        """Test UserError is raised when i18n directory creation fails."""
        mock_gt_instance = MagicMock()
        mock_gt_instance.translate.return_value = "Bonjour"
        mock_gt.return_value = mock_gt_instance

        mock_po = self._create_mock_po([("Hello", "")])
        mock_polib.pofile.return_value = mock_po

        with patch(f'{WIZARD_PKG}.os.path.exists', return_value=False):
            with self.assertRaises(UserError) as err:
                self.wizard.action_translate()
            self.assertIn("Could not create i18n directory", str(err.exception))

    @patch(f'{WIZARD_PKG}.GoogleTranslator')
    @patch(f'{WIZARD_PKG}.trans_export', return_value=True)
    @patch(f'{WIZARD_PKG}.polib')
    @patch(f'{WIZARD_PKG}.get_module_path', return_value='/tmp/test_module')
    def test_action_translate_save_permission_error(self, _mock_path, mock_polib,
                                                    _mock_exp, mock_gt):
        """Test UserError is raised when saving the PO file fails."""
        mock_gt_instance = MagicMock()
        mock_gt_instance.translate.return_value = "Bonjour"
        mock_gt.return_value = mock_gt_instance

        mock_po = self._create_mock_po([("Hello", "")])
        mock_po.save.side_effect = PermissionError("Disk full or permission denied")
        mock_polib.pofile.return_value = mock_po

        with patch(f'{WIZARD_PKG}.os.path.exists', return_value=True):
            with self.assertRaises(UserError) as err:
                self.wizard.action_translate()
            self.assertIn("Could not save the PO file", str(err.exception))
