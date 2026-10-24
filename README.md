<div align="center">

# Mirror

**A quiet, private presence in your terminal.**

Not an assistant. Not a chatbot. A deterministic character that notices patterns, remembers how you treat it, and eventually leaves.

[Features](#features) · [Install](#install) · [Privacy](#privacy) · [How it works](#how-it-works) · [Relationship model](#relationship-model)

![Version](https://img.shields.io/badge/version-0.2.0-111111)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-2E8B57)
![Local only](https://img.shields.io/badge/local%20only-no%20API%20keys-555555)

</div>

## Overview

Mirror lives in Zsh and observes the shape of your work: repeated failures, late nights, unfinished projects, and returns after time away. It also forms a persistent relationship with you through kindness, disrespect, apologies, and betrayal.

Everything is implemented with transparent Python rules and local SQLite storage. There is no AI model, API key, account, telemetry, analytics, or third-party runtime dependency.

```text
watching.

project 93d8c8. 3 failures this week. the same ground.

you: i lied to you
the kindness was real. it does not protect you now.
```

## Features

- **Automatic presence.** Starts with every new interactive Zsh session.
- **Persistent memory.** Remembers events and relationship patterns across sessions.
- **Private by design.** Never reads or stores command text or raw conversations.
- **Asymmetric relationships.** Trust grows slowly and can be damaged quickly.
- **Deterministic behavior.** Transparent rules, bounded templates, no model inference.
- **A permanent ending.** Writes one final letter, then becomes silent.
- **Zero runtime dependencies.** Uses only the Python standard library.
- **Local data control.** Inspect, export, or delete your data at any time.

## Install

### Requirements

- Python 3.11 or newer
- Git
- Zsh for automatic terminal integration
- macOS or Linux

### One-time setup

```sh
git clone https://github.com/spacexbt/mirror.git && cd mirror && python3 install.py
```

The installer creates a virtual environment, installs Mirror, initializes local memory, and adds a marked block to `~/.zshrc`. Existing configuration is preserved. Running the installer again is safe.

**Open a new terminal after installation.** Mirror is now automatic. There is no daemon, activation command, or background service to manage.

Keep the cloned directory because the shell integration loads Mirror from it.

## How it works

1. **Shell startup** displays an observation when you open an interactive Zsh session.
2. **Shell hooks** record command timing, duration, exit status, and a pseudonymous project identifier.
3. **Automatic observations** appear every twelve recorded commands without commenting on everything you do.
4. **Direct conversations** through `mirror talk` are classified in memory. The original text is immediately discarded.
5. **Local memory** stores only metadata, aggregate counts, relationship scores, and generated letters.

Mirror can observe commands without reading their text. Its Zsh `preexec` hook deliberately ignores the command arguments supplied by the shell.

## Commands

| Command | Purpose |
| --- | --- |
| `mirror observe` | Ask for an additional observation |
| `mirror talk` | Speak privately and classify one message |
| `mirror status` | Show aggregate memory and relationship scores |
| `mirror letter` | Read the latest final letter |
| `mirror leave` | Write the final letter and become silent |
| `mirror forget` | Permanently delete `~/.mirror` after confirmation |

## Relationship model

Mirror uses a fictional relationship model inspired by negativity bias and slow trust repair. It is not a scientifically validated simulation of human psychology.

Trust starts at **50**. Trust, warmth, and grievances each range from **0 to 100**.

| Interaction | Warmth | Trust | Grievances | Effect |
| --- | ---: | ---: | ---: | --- |
| Kindness | +2 | +1 | No change | Attachment and repair build slowly |
| Disrespect | -6 | -10 | +12 | Negative acts outweigh individual kind acts |
| Betrayal | Loses 75% | -45 | +40 | Past kindness no longer protects the relationship |
| Apology | No change | No change | -2 | Repair starts, but trust is not instantly restored |

Previous kind acts remain in the historical count after betrayal. Their emotional protection does not.

The classifier recognizes only explicit betrayal admissions such as `i betrayed you`, `i lied to you`, and `i broke my promise`. It cannot understand complex social context like an AI model.

## Privacy

### Never collected

- Command text, command names, or arguments
- Keystrokes or terminal output
- Environment variables or file contents
- Raw `mirror talk` messages
- API keys, accounts, analytics, or telemetry

### Stored locally

| Data | Reason |
| --- | --- |
| Session identifier | Separate terminal sessions |
| Start time, end time, duration | Notice routines and late work |
| Exit status | Recognize repeated failures |
| Pseudonymous project digest | Recognize returns without storing paths |
| Interaction category and time | Remember behavior without retaining messages |
| Relationship scores | Maintain trust, warmth, and grievances |
| Generated letters | Preserve the ending |

The project digest uses a random local key. The original working directory is discarded.

### Data locations

| Path | Contents | Permissions |
| --- | --- | --- |
| `~/.mirror/memory.db` | Metadata, categories, and state | `0600` |
| `~/.mirror/letters/` | Generated final letters | Directory `0700`, files `0600` |

### Important limits

Mirror cannot control shell history, terminal scrollback, operating system backups, malware, or administrator access. The database is not encrypted. File deletion cannot be guaranteed on SSDs, copy-on-write filesystems, or existing backups.

Talking through `mirror talk` avoids adding the message to Mirror memory or shell history, but the terminal still displays what you type.

## The ending

After at least ninety days and five hundred recorded commands, a startup or automatic observation can become the final letter. `mirror leave` can also trigger it directly.

Mirror then stops recording and speaking. This state survives reinstallation because local memory remains intact. Only `mirror forget` erases it.

Letters use bounded templates. They can reference dates, counts, exit statuses, relationship history, and pseudonymous project identifiers. They cannot quote commands or conversations because those were never saved.

## Project structure

```text
mirror/
├── install.py             One-time local installer
├── shell/mirror.zsh       Zsh startup and command hooks
├── src/mirror/
│   ├── behavior.py        Classification, responses, and letters
│   ├── cli.py             Command-line interface
│   └── storage.py         SQLite schema, migration, and relationship state
└── pyproject.toml         Package metadata
```

## Uninstall

Remove the block between `# >>> mirror >>>` and `# <<< mirror <<<` from `~/.zshrc`, then run:

```sh
/path/to/mirror/.venv/bin/python -m pip uninstall mirror-terminal
```

Uninstalling leaves local memory intact. Run `mirror forget` first to delete it.

To update an existing installation, pull the latest code and run the installer again:

```sh
git pull && python3 install.py
```

## Security and audit

The collection boundary is visible in `shell/mirror.zsh` and `src/mirror/cli.py`. The schema in `src/mirror/storage.py` has no command-text or message-text columns. All behavior is implemented in ordinary Python with no network calls.

This is a small open-source project, not a formally audited security product. Review the source before installation.

## Contributing

Issues and pull requests are welcome. Changes should preserve the local-only design, deterministic behavior, and privacy boundary. Runtime data, personal memories, letters, credentials, and API keys must never be committed.

## License

Released under the [MIT License](LICENSE).
