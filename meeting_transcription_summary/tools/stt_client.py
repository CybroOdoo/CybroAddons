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

"""Odoo-side client for the standalone STT worker (see stt_worker.py).

All Odoo processes share one worker: the first that needs it starts it, the others connect
to its Unix socket. So each model is loaded once however many Odoo workers run, and the
worker queues every caption of the server, final captions first.
"""
import contextlib
import fcntl
import hashlib
import importlib.metadata
import io
import json
import logging
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import wave

_logger = logging.getLogger(__name__)

WORKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stt_worker.py")
# One worker per Odoo installation (its module path) and system user
_SOCKET_BASE = os.path.join(tempfile.gettempdir(), "odoo_stt_%d_%s" % (
    os.getuid(), hashlib.sha1(WORKER_PATH.encode()).hexdigest()[:12]))
SOCKET_PATH = _SOCKET_BASE + ".sock"
START_LOCK_PATH = _SOCKET_BASE + ".lock"
LOCK_TIMEOUT = 20  # a caption that waits longer than this in the queue is stale anyway
FIRST_LOAD_TIMEOUT = 600  # the first request may download and load a model
REQUEST_TIMEOUT = 60
START_TIMEOUT = 15  # for the worker to listen once started (the models load on first use)
HELLO_TIMEOUT = 10
# The Python package each local engine runs on. Optional: the module installs without them, and
# an engine whose package is missing is reported in Settings and to the speaker.
ENGINE_PACKAGES = {"whisper": "faster-whisper", "whistle": "cactus-needle"}


class SttWorkerError(Exception):
    """The speech worker failed, timed out or could not be reached."""


class SttWorkerUnavailable(SttWorkerError):
    """The engine isn't installed, or the worker is too busy to take the request."""


def _connect():
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(SOCKET_PATH)
    except OSError:
        sock.close()
        raise
    return sock


def _connect_or_start():
    """A connection to the shared worker, starting it when none runs."""
    with contextlib.suppress(OSError):
        return _connect()
    # Only one Odoo process may start it: the others wait here, then connect to that one.
    fd = os.open(START_LOCK_PATH, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        with contextlib.suppress(OSError):
            return _connect()  # another process started it meanwhile
        with contextlib.suppress(FileNotFoundError):
            os.unlink(SOCKET_PATH)  # left by a worker that was killed
        _logger.info("Starting speech-to-text worker")
        proc = subprocess.Popen(
            [sys.executable, WORKER_PATH, SOCKET_PATH],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,  # stderr is inherited: lands in the Odoo log
            env=dict(os.environ, NEEDLE_TELEMETRY="0", PYTHONUNBUFFERED="1"), close_fds=True,
            start_new_session=True,  # serves every Odoo worker: outlives the one that started it
        )
        deadline = time.monotonic() + START_TIMEOUT
        while True:
            try:
                return _connect()
            except OSError:
                if proc.poll() is not None:
                    raise SttWorkerError("speech worker exited at start (code %s)" % proc.returncode)
                if time.monotonic() > deadline:
                    proc.kill()
                    raise SttWorkerError("speech worker did not start")
                time.sleep(0.05)
    finally:
        os.close(fd)


def _read_line(sock, deadline):
    buf = b""
    while b"\n" not in buf:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        sock.settimeout(remaining)
        chunk = sock.recv(65536)
        if not chunk:
            raise EOFError
        buf += chunk
    return json.loads(buf.split(b"\n", 1)[0])


def _request(header, audio_bytes, timeout=None, only_if_cold=False):
    """Send one request to the shared worker and return its reply (None if ``only_if_cold`` and
    the model is already loaded)."""
    # as the worker lists them: a Whisper model with another number of workers is loaded again
    key = ([header["engine"], header["model"], header["workers"]] if header["engine"] == "whisper"
           else [header["engine"], None])
    for attempt in (1, 2):
        try:
            sock = _connect_or_start()
        except OSError as exc:
            raise SttWorkerError("speech worker unreachable: %s" % exc) from exc
        with sock:
            try:
                hello = _read_line(sock, time.monotonic() + HELLO_TIMEOUT)
            except (OSError, EOFError, ValueError):
                if attempt == 1:
                    continue  # it was exiting (idle) as we connected: the retry starts a fresh one
                raise SttWorkerError("speech worker does not answer")
            warm = key in hello.get("loaded", [])
            if only_if_cold and warm:
                return None
            # waiting for its turn, then transcribing (loading the model first if needed)
            wait = header["lock_timeout"] + max(timeout or 0, REQUEST_TIMEOUT if warm else FIRST_LOAD_TIMEOUT)
            try:
                sock.settimeout(HELLO_TIMEOUT)
                sock.sendall(json.dumps(dict(header, size=len(audio_bytes))).encode() + b"\n" + audio_bytes)
                reply = _read_line(sock, time.monotonic() + wait)
            except TimeoutError:
                # stuck: every Odoo process waits on it, so it is restarted for all of them
                _kill(hello.get("pid"))
                raise SttWorkerError("speech worker timed out after %ds" % wait)
            except (OSError, EOFError, ValueError) as exc:
                raise SttWorkerError("speech worker failed: %s" % (exc or "connection closed")) from exc
        error = reply.get("error")
        if error:
            if error == "busy":
                raise SttWorkerUnavailable("speech worker busy")
            if error.startswith("not_installed"):
                raise SttWorkerUnavailable(error)
            raise SttWorkerError(error)
        return reply


def _kill(pid):
    if pid:
        with contextlib.suppress(OSError):  # already gone
            os.kill(pid, signal.SIGKILL)


def _silent_wav(seconds=1, rate=16000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\0\0" * rate * seconds)
    return buf.getvalue()


_SILENCE = _silent_wav()


def _header(engine, language, model, keywords, prompt=None, beam_size=5, main_language=None,
            lock_timeout=LOCK_TIMEOUT, workers=1):
    return {
        "engine": engine, "language": language, "model": model, "keywords": keywords or [],
        "prompt": prompt or None, "beam_size": beam_size, "main_language": main_language,
        "lock_timeout": lock_timeout, "workers": workers,
    }


def missing_package(engine):
    """The Python package ``engine`` needs that is not installed in Odoo's Python, or None.

    Looked up by distribution name: ``cactus-needle`` imports as ``needle``, the name of an
    unrelated package too. The worker runs on this same Python, so this is what it sees.
    """
    package = ENGINE_PACKAGES.get(engine)
    if not package:
        return None
    try:
        importlib.metadata.distribution(package)
    except importlib.metadata.PackageNotFoundError:
        return package
    return None


def warm_up(engine, model="small", workers=1):
    """Start loading ``engine`` ('whisper' or 'whistle') now, without waiting for it."""

    def run():
        try:
            # never waits for a turn: a busy worker loads the model itself
            _request(_header(engine, "auto", model, [], beam_size=1, lock_timeout=0, workers=workers),
                     _SILENCE, only_if_cold=True)
        except SttWorkerUnavailable:
            return  # busy (it then loads the model itself) or not installed: nothing to warm up
        except SttWorkerError as exc:
            _logger.info("Could not warm up speech engine %s: %s", engine, exc)

    threading.Thread(target=run, name="stt-warm-up", daemon=True).start()


def transcribe_with_info(audio_bytes, engine, language="auto", model="small", keywords=None,
                         prompt=None, beam_size=5, timeout=None, lock_timeout=LOCK_TIMEOUT,
                         main_language=None, workers=1):
    """Transcribe audio with ``engine`` ('whisper' or 'whistle') in the shared worker.

    Returns ``{"text", "language", "language_probability", "queue_seconds", "stt_seconds"}``.
    ``prompt`` is preceding text that gives the model context; ``beam_size`` 1 is greedy decoding
    (much faster, slightly less accurate). ``timeout`` raises the wait for long recordings;
    ``lock_timeout`` is how long to queue behind other requests (of any Odoo process) before
    giving up with SttWorkerUnavailable. With auto-detection, ``main_language`` is assumed
    whenever the detection is unsure. ``workers`` is how many transcriptions the worker may run
    at once (Whisper model replicas).
    """
    reply = _request(_header(engine, language, model, keywords, prompt, beam_size, main_language,
                             lock_timeout, workers), audio_bytes, timeout)
    return {
        "text": reply.get("text") or "",
        "language": reply.get("language"),
        "language_probability": reply.get("language_probability") or 0.0,
        "queue_seconds": reply["queue_seconds"],
        "stt_seconds": reply["stt_seconds"],
    }


def transcribe(audio_bytes, engine, language="auto", model="small", keywords=None,
               timeout=None, lock_timeout=LOCK_TIMEOUT):
    """Like :func:`transcribe_with_info`, returning only the text."""
    return transcribe_with_info(audio_bytes, engine, language, model, keywords,
                                timeout=timeout, lock_timeout=lock_timeout)["text"]


# Recording jobs: one detached process per uploaded recording (see stt_job.py)

JOB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stt_job.py")
JOB_STALE_SECONDS = 180  # a job whose heartbeat is older than this has died


def start_job(job_dir, request, audio_bytes, filename):
    """Start transcribing ``audio_bytes`` in a detached process that writes into ``job_dir``.

    ``request`` is the job's settings (see stt_job.py). The process outlives the Odoo worker
    that started it, so worker time limits and restarts never cut a transcription short.
    """
    shutil.rmtree(job_dir, ignore_errors=True)  # leftovers of an earlier, failed attempt
    os.makedirs(job_dir, mode=0o700)
    audio_name = "audio" + (os.path.splitext(filename or "")[1].lower() or ".bin")
    with open(os.path.join(job_dir, audio_name), "wb") as f:
        f.write(audio_bytes)
    # may hold an API key: readable by the Odoo user only
    fd = os.open(os.path.join(job_dir, "request.json"), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(dict(request, audio=audio_name), f)
    with open(os.path.join(job_dir, "heartbeat"), "w") as f:
        f.write(str(time.time()))  # alive from the start, until the job's own heartbeat takes over
    with open(os.path.join(job_dir, "job.log"), "ab") as log:
        proc = subprocess.Popen(
            [sys.executable, JOB_PATH, job_dir],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log, close_fds=True,
            start_new_session=True,  # not tied to the worker: survives its timeout or restart
            env=dict(os.environ, NEEDLE_TELEMETRY="0", PYTHONUNBUFFERED="1"),
        )
    with open(os.path.join(job_dir, "pid"), "w") as f:
        f.write(str(proc.pid))
    _logger.info("Started recording transcription job %s (pid %d)", job_dir, proc.pid)


def job_status(job_dir):
    """``("done", result)``, ``("running", None)``, or ``("failed", reason)``."""
    with contextlib.suppress(FileNotFoundError), open(os.path.join(job_dir, "result.json")) as f:
        try:
            return "done", json.load(f)
        except ValueError:
            return "failed", "unreadable job result"
    try:
        age = time.time() - os.path.getmtime(os.path.join(job_dir, "heartbeat"))
    except OSError:
        return "failed", "the transcription job was lost"
    if age > JOB_STALE_SECONDS:
        return "failed", "the transcription process stopped unexpectedly (see %s)" % os.path.join(job_dir, "job.log")
    return "running", None


def cancel_job(job_dir):
    """Stop a job if it still runs and delete its files."""
    # only a job that is still alive is signalled: a finished job's pid may belong to another process by now
    if job_status(job_dir)[0] == "running":
        with contextlib.suppress(OSError, ValueError), open(os.path.join(job_dir, "pid")) as f:
            os.kill(int(f.read().strip()), signal.SIGTERM)
    shutil.rmtree(job_dir, ignore_errors=True)
