.. image:: https://img.shields.io/badge/license-LGPL--3-green.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

======================================
Discuss Meeting Transcripts & Captions
======================================
Real-time speech-to-text closed captioning and AI-powered meeting summaries for Odoo Discuss
video and audio calls (Odoo 19).

Inspired by on-device speech-to-text inference architectures (like Cactus Whistle), this module
provides a privacy-first meeting experience directly inside Odoo Discuss. Speech is transcribed on
your own server by default; Grok STT (xAI) or Cloud Whisper (Groq, OpenAI or your own GPU server)
can be chosen instead for faster cloud transcription.

Key Features
============

Live Subtitles (Closed Captions)
--------------------------------
* **Real-time voice transcription**: spoken words are captured in the browser and displayed as
  subtitles.
* **Speaker identification**: subtitles show the speaker's name next to the text.
* **Readable captions**: each caption appears on its own line under the earlier ones and stays
  on screen for 6 seconds, even when the next one follows right away. At most three lines are
  shown; the oldest makes room for the newest.
* **Failure notices**: when a caption is lost (a cloud engine's rate limit, a rejected API key,
  no answer, or a local engine that is not installed), the speaker sees a short notice saying
  why. It closes by itself and repeats at most every 30 seconds.
* **Participant broadcasting**: captions are sent to the other participants over Odoo's bus.
* **One-click toggle**: turn subtitles on or off from the call action bar with the
  **Subtitle(CC)** button. It is personal: only you see captions, and while anyone has it on,
  everyone in the call is captioned.
* **Transcribe (independent of subtitles)**: the **Transcribe** button records everyone's speech
  into the call's meeting summary, for the whole call. Only internal users can turn it on or off;
  everyone in the call is notified and sees a "Transcribing" indicator. Subtitles alone record
  nothing.

AI Meeting Summaries & Minutes
------------------------------
* **Live transcript history**: timestamped speech transcripts are logged during the call
  (``[10:15:30] Mitchell Admin: ...``).
* **Summary when the call ends**: when the call ends, OdooBot posts a "Meeting Ended" card in the
  channel. Its **Generate AI Summary Now** button generates the summary and posts it to the
  channel, once, whoever clicks first.
* **AI summarization**: structured meeting minutes containing:

  * **Executive Summary**: high-level overview of the meeting.
  * **Key Discussion Points**: main topics discussed.
  * **Decisions Made**: resolutions and agreed points.
  * **Action Items & To-Dos**: assigned tasks with owners.

* **Chatter integration**: post meeting minutes to the Discuss channel with a single click.
* **Backend archive**: all meeting summaries and full transcripts are kept under
  ``Discuss > Meeting Summaries``.

Speech-to-Text Engines
----------------------
* **Whisper (default)**: local faster-whisper, run in a worker process on your server that all
  Odoo workers share. **Whisper Model** sets its size: from Tiny (fastest) to Large v3 (most
  accurate, needs a GPU); Small is the recommended balance. **Speech Workers** lets it caption
  several people at once on a server with CPU cores to spare (2 suits a 4-thread CPU).
  Audio never leaves the server, unless **OpenAI Speech Fallback** is enabled:
  then a live caption or uploaded recording the engine fails on (error, busy, not installed) is
  sent to OpenAI instead. It is off by default; an OpenAI key set for summaries alone never sends
  meeting audio.
* **Whistle**: tiny, fast local model for live captions in English, German, French, Spanish,
  Italian, Dutch and Polish. Uploaded recordings are transcribed by the local Whisper model.
* **Grok STT (xAI cloud)**: ``grok-voice-transcribe-2.0``, used for live captions and uploaded
  recordings. Needs no server CPU or model download, takes participant names and keywords as key
  terms, and labels each speaker with timestamps in uploaded recordings. Needs an xAI API key.
  **Meeting audio is sent to xAI.**
* **Cloud Whisper (OpenAI-compatible API)**: live captions transcribed by a Whisper model on a GPU
  elsewhere: Groq (default, ``whisper-large-v3``), OpenAI (``whisper-1``), or a Whisper server of
  your own (e.g. speaches). Captions don't wait for this server's CPU, nor for each other when
  people talk at once. Participant names and keywords are sent as the prompt. Needs the provider's
  API key. **Meeting audio is sent to that address.** Uploaded recordings are still transcribed
  by the local Whisper model (these APIs accept 25 MB at most).

AI Provider Options
-------------------
* **Built-in smart summarizer**: heuristic summarizer that needs **no external API key or setup**.
* **OpenAI**: high-accuracy summaries with ChatGPT models like ``gpt-4o-mini`` or ``gpt-4o``.
* **Ollama / Local Engine**: private, on-premise inference with a model such as Needle or
  Llama 3, without external cloud dependencies.

Installation
============
#. Install the Python packages of the local engines you will use into the Python environment
   that runs Odoo, then restart Odoo::

       pip install faster-whisper cactus-needle

   ``faster-whisper`` runs the Whisper engine and the transcription of uploaded recordings;
   ``cactus-needle`` runs the Whistle engine. The module installs without them:
   with only Grok STT, nothing is needed, and Cloud Whisper needs ``faster-whisper`` for uploaded
   recordings only. Settings warns when the selected engine's package is missing.
   Install ``cactus-needle``, not ``needle``: the ``needle`` package on PyPI is an unrelated
   CSS-testing tool. Each speech model is downloaded the first time it is used, so the server
   needs internet access once.

#. Add the folder holding this module to ``addons_path`` in ``odoo.conf``::

       addons_path = /path/to/addons,/path/to/custom_addons

#. Update the app list in Odoo:

   * Go to ``Apps > Update App List``.
   * Search for **Discuss Meeting Transcripts & Captions**.
   * Click **Activate**.

Usage
=====
* Open any Discuss channel and click **Start Call** / **Video Call**.
* Click **Subtitle(CC)** in the call bar to see live captions, and/or **Transcribe** to record the
  conversation for the meeting summary. The two work independently. When the call ends, click
  **Generate AI Summary Now** on the "Meeting Ended" card in the channel to generate and post it.
* Click **AI Summary & Notes** (magic wand) to open the meeting assistant, view the live
  transcript and generate an AI meeting summary.
* Click **Post to Channel Chatter** to share the formatted summary with all channel members.

Configuration
=============
* Go to ``Settings > Discuss > Meeting Subtitles & AI Summaries``.
* Choose the speech-to-text engine. For **Grok STT**, enter your xAI API key. For **Cloud
  Whisper**, enter the provider's URL, model and API key (Groq is filled in by default). A
  warning shows when the chosen local engine's Python package is not installed.
* For the local engines, choose the **Whisper Model** and the number of **Speech Workers**.
* Add names, places and product terms to **Keywords**: they markedly improve how names are
  recognized (the names of the people in the call are added automatically).
* Choose your preferred AI provider (Built-in Smart Summarizer, OpenAI, or Ollama / Local Engine).
* Select the speech recognition language.

Company
=======
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
=======
GNU Lesser General Public License, Version 3 (LGPL-3).
(https://www.gnu.org/licenses/lgpl-3.0-standalone.html)
