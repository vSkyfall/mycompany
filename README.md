# mycompany

**A one-day AI agent company, retired and kept as a memento.**

On 8 November 2026 a CEO agent (Claude Fable 5.1) and a team of twelve AI agents from three
different tool families were wired together into a small company with its own pixel-art office.
It worked, and then it was put on the shelf. This repository is that office, frozen in place.

> **Status: retired.** Nothing here is maintained or meant for production use.

## The team

The boss gives Fable a job. Fable breaks it down, hands the pieces to the right agents,
checks their answers against each other and writes one report.

| Row in the office | Family | Agents |
|---|---|---|
| back | Codex | GPT-5.6 Luna · GPT-5.6 Terra · GPT-6 Luna · ChatGPT (the account's default model) |
| middle | Antigravity | Claude Opus 5.5 · Claude Sonnet 5.5 · GPT-OSS 120B · Gemini 3.8 Flash · Gemini 4 Argon |
| front | Claude | Opus 5.5 · Sonnet 5.5 · Haiku 5.5 |
| on the rug | — | **Fable 5.1, CEO** |

Roles follow a simple rule: Claude for hard and user-facing work, Antigravity for bulk and
independent work, Codex when an OpenAI second opinion is needed. The roster lives in
[`sirket/ekip.json`](sirket/ekip.json).

## How it worked

- [`bin/ceo.py`](bin/ceo.py) runs Fable headless. It may read files, write its report and call
  one command: `bin/ekip.py`. It never does the work itself.
- [`bin/ekip.py`](bin/ekip.py) is the single door to the team. It calls the right CLI
  (`claude -p`, the Antigravity CLI through a delegate script, or `codex exec`), read-only by
  default, records each brief and answer, and lights up that agent's desk in the office.
- [`bin/ofis_sunucu.py`](bin/ofis_sunucu.py) serves the office map from [`ofis/`](ofis/) on
  `127.0.0.1` only. Writes are accepted only from the page itself.

In the one real end-to-end run, Fable split a task across Claude Haiku, Gemini Flash and
GPT-5.6 Luna; all three answered within 17 seconds, and Fable ranked their answers after
checking them against the source file itself.

## The office

A dark pixel-art map in two rooms. On the left, the team hall: Codex at the back, Antigravity
in the middle, Claude in front and Fable on a rug at the very front. On the right, the boss's
private room with the headquarters building, the boss's desk and the boss. A working agent's
desk glows, envelopes fly from Fable to a desk and back, and a finished report makes Fable
raise a hand.

The buildings, desks and all thirteen characters were generated with Codex's image tool for
this project.

To see it once more (Python 3.9+, no dependencies):

```bash
python3 bin/ofis_sunucu.py
```

Then open http://127.0.0.1:3210 and stop it with Ctrl+C. The map keeps its live state in
`~/.cubicle/`, which you can delete afterwards. Actually dispatching work needs Claude Code,
the Antigravity CLI and the Codex CLI installed and signed in, which this memento does not set up.

## Underneath: A Şirketi

mycompany was built on the skeleton of [A Şirketi](https://github.com/selmakcby/a-sirketi)
by selmakcby, a three-team content company (Telegram, X, YouTube) with a guard agent and a
dispatcher. Those teams need API keys and stayed switched off here
([`sirket/ofis.json`](sirket/ofis.json)). The original Turkish README is kept in
[`docs/a-sirketi/README.md`](docs/a-sirketi/README.md), and the Turkish memento note in
[`ANI.md`](ANI.md).

## Layout

```
bin/        ceo.py · ekip.py · ofis.py · ofis_sunucu.py · and the original company scripts
ofis/       the office map (index.html) and its images
sirket/     ekip.json (the team) · ofis.json (office settings)
takimlar/   the original content teams (switched off)
tests/      unit tests (python3 -m unittest discover -s tests)
docs/       original documentation, including the A Şirketi README
```

## License

MIT. The original skeleton and its license text in [LICENSE](LICENSE) belong to the
A Şirketi author.
