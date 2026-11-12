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

import contextlib
import difflib
import logging
import os
import re
from unittest.mock import patch
from urllib.parse import urlsplit

from odoo.tests import HttpCase, tagged
from odoo.tests.common import ChromeBrowser

from odoo.addons.web.tests.test_js import HOOTCommon, unit_test_error_checker

_logger = logging.getLogger(__name__)

# Directory to write the JavaScript coverage report to, e.g.
#   ODOO_JS_COVERAGE=/tmp/js_coverage odoo-bin ... --test-tags /meeting_transcription_summary:TestMeetingJs
JS_COVERAGE_DIR = os.environ.get('ODOO_JS_COVERAGE')
MODULE_SRC = '/meeting_transcription_summary/static/src/'
# how each file starts in a bundle served with debug=assets
FILE_HEADER = re.compile(r'/\*+\n\*  Filepath: (\S+)\s+\*\n\*  Lines: \d+\s+\*\n\*+/\n')
# lines that are not statements: blank, comments, closing brackets
NOT_CODE = re.compile(r'^\s*(?:$|//|/\*|\*|[\]\)\};,]+$)')


@tagged('post_install', '-at_install')
class TestMeetingJs(HttpCase):
    """The module's JavaScript unit tests (static/tests/*.test.js), run with Hoot in a browser."""

    def test_unit_tests(self):
        # only this module's suite: Hoot selects a suite by the hash of its name
        suite = HOOTCommon._generate_hash(self, '@meeting_transcription_summary')
        # Hoot's mock server takes the page's user for its own admin: log in as the real one,
        # whatever its login (browser_js signs in with the login as password; rolled back after)
        admin = self.env.ref('base.user_admin')
        admin.password = admin.login
        url = f'/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&id={suite}'
        with contextlib.ExitStack() as stack:
            if JS_COVERAGE_DIR:
                url += '&debug=assets'  # files one by one, not minified: coverage maps back to them
                scripts = stack.enter_context(self._js_coverage())
            self.browser_js(
                url, "", "", login=admin.login, timeout=1800,
                success_signal="[HOOT] Test suite succeeded", error_checker=unit_test_error_checker,
            )
        if JS_COVERAGE_DIR:
            self._write_js_coverage(scripts)

    @contextlib.contextmanager
    def _js_coverage(self):
        """Have Chrome count what runs (V8 precise coverage), from page load to the end of the tests."""
        scripts = []
        navigate_to, wait_code_ok = ChromeBrowser.navigate_to, ChromeBrowser._wait_code_ok

        def start_then_navigate(browser, url, wait_stop=False):
            browser._websocket_request('Profiler.enable')
            browser._websocket_request('Profiler.startPreciseCoverage', params={'callCount': True, 'detailed': True})
            return navigate_to(browser, url, wait_stop)

        def run_then_collect(browser, code, timeout, error_checker=None):
            wait_code_ok(browser, code, timeout, error_checker)
            scripts.extend(browser._websocket_request('Profiler.takePreciseCoverage', timeout=60)['result'])

        with patch.object(ChromeBrowser, 'navigate_to', start_then_navigate), \
                patch.object(ChromeBrowser, '_wait_code_ok', run_then_collect):
            yield scripts

    def _write_js_coverage(self, scripts):
        """Line coverage of each of the module's JS files, written to JS_COVERAGE_DIR/js_coverage.txt."""
        files = {}
        for script in scripts:
            if '/web/assets/' not in script['url'] or not script['url'].endswith('.js'):
                continue
            source = self.url_open(urlsplit(script['url']).path).text
            if MODULE_SRC not in source:
                continue
            ranges = [r for function in script['functions'] for r in function['ranges']]
            headers = list(FILE_HEADER.finditer(source))
            for header, following in zip(headers, headers[1:] + [None]):
                path = header.group(1)
                if MODULE_SRC in path and path.endswith('.js'):
                    end = following.start() if following else len(source)
                    counts = _line_counts(source, header.end(), end, ranges)
                    files[path] = _to_source_lines(counts, source[header.end():end],
                                                   self.url_open(path).text)

        lines = ["%-60s %6s %6s %6s   %s" % ("File", "Lines", "Miss", "Cover", "Missing")]
        total = missed_total = 0
        for path, counts in sorted(files.items()):
            missed = [n for n, count in counts if not count]
            total += len(counts)
            missed_total += len(missed)
            lines.append("%-60s %6d %6d %5d%%   %s" % (
                path.replace(MODULE_SRC, ''), len(counts), len(missed),
                100 * (len(counts) - len(missed)) // max(len(counts), 1), _ranges(missed)))
        lines.append("%-60s %6d %6d %5d%%" % ("TOTAL", total, missed_total,
                                              100 * (total - missed_total) // max(total, 1)))
        os.makedirs(JS_COVERAGE_DIR, exist_ok=True)
        with open(os.path.join(JS_COVERAGE_DIR, 'js_coverage.txt'), 'w') as f:
            f.write("\n".join(lines) + "\n")
        _logger.info("JavaScript coverage:\n%s", "\n".join(lines))


def _line_counts(source, start, end, ranges):
    """``[(line number, times run)]`` for each statement line of ``source[start:end]``.

    A line counts as run when the innermost V8 block holding its first character ran. V8 gives
    offsets in UTF-16 code units, hence the conversion.
    """
    utf16 = len(source[:start].encode('utf-16-le')) // 2
    utf16_end = utf16 + len(source[start:end].encode('utf-16-le')) // 2
    ranges = [r for r in ranges if r['startOffset'] < utf16_end and r['endOffset'] > utf16]
    counts = []
    for number, line in enumerate(source[start:end].split('\n'), 1):
        if not NOT_CODE.match(line):
            offset = utf16 + len(line) - len(line.lstrip())
            holding = [r for r in ranges if r['startOffset'] <= offset < r['endOffset']]
            innermost = min(holding, key=lambda r: r['endOffset'] - r['startOffset'], default=None)
            counts.append((number, innermost['count'] if innermost else 0))
        utf16 += len((line + '\n').encode('utf-16-le')) // 2
    return counts


def _to_source_lines(counts, bundled, original):
    """``counts`` renumbered as lines of the original file.

    The bundle holds the file as transpiled by Odoo (imports and exports rewritten, a module
    wrapper added): its lines are matched to the original's by their text. Lines only in the
    transpiled version (the wrapper, rewritten imports) are left out.
    """
    bundled_lines = [line.strip() for line in bundled.split('\n')]
    original_lines = [line.strip() for line in original.split('\n')]
    to_original = {}
    matcher = difflib.SequenceMatcher(None, bundled_lines, original_lines, autojunk=False)
    for block in matcher.get_matching_blocks():
        for i in range(block.size):
            to_original[block.a + i + 1] = block.b + i + 1
    return [(to_original[number], count) for number, count in counts if number in to_original]


def _ranges(numbers):
    """``[3, 4, 5, 9]`` -> ``'3-5, 9'``."""
    spans = []
    for n in numbers:
        if spans and spans[-1][1] == n - 1:
            spans[-1][1] = n
        else:
            spans.append([n, n])
    return ", ".join(str(a) if a == b else "%d-%d" % (a, b) for a, b in spans)
