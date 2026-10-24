# Mirror

A quiet, deterministic presence in your terminal. It notices repeated failures, late work, returning projects, cruelty, apologies, and kindness. It remembers patterns rather than collecting your terminal.

Mirror runs entirely on your computer. There is no AI model, API key, account, telemetry, analytics, network access, or third-party runtime dependency.

## Privacy

**Mirror never reads or stores command text.** Its Zsh `preexec` function records a start time without reading the arguments Zsh gives it. No keystrokes, terminal output, environment variables, file contents, command names, or command arguments are collected.

For each executed command, Mirror stores only:

- A random shell-session identifier.
- Start and end timestamps.
- Exit status.
- A keyed, pseudonymous digest of the working directory. The path itself is discarded.

The digest lets Mirror recognize a return to the same project without retaining its name or location. The key is generated locally and stored in the owner-only database.

`mirror talk` reads one line interactively. It classifies the line as neutral, apology, abuse, kindness, or betrayal in memory, then discards the text. Only that category and the time are stored. The classifier is deliberately simple and can be wrong; it does not understand meaning like an AI model. Betrayal is recognized only from explicit admissions such as `i betrayed you`, `i lied to you`, or `i broke my promise`.

The local database is `~/.mirror/memory.db`. Final letters are in `~/.mirror/letters/`. The directory is mode `0700` and files are mode `0600`.

## Relationship model

Mirror uses a transparent fictional model inspired by negativity bias and slow trust repair. It is not a scientifically validated simulation of human psychology. Trust starts at 50; trust, warmth, and grievances each range from 0 to 100.

- **Kindness:** warmth +2, trust +1. Attachment and repair accumulate slowly.
- **Disrespect:** warmth -6, grievances +12, trust -10. Negative acts outweigh individual kind acts.
- **Betrayal:** only 25% of current warmth remains, grievances +40, trust -45. Previous kind acts remain in the historical count but no longer protect the current relationship.
- **Apology:** grievances -2, with no immediate trust or warmth restoration. Later consistent kindness is required for repair.

`mirror status` exposes the current scores and betrayal count. Exact formulas are in `src/mirror/storage.py`; response rules are in `src/mirror/behavior.py`.

### What Mirror cannot protect

Mirror cannot erase data that other software has already collected. Your shell may save commands in its history, your terminal may keep scrollback, and your operating system may keep backups. Talking through `mirror talk` avoids adding the message to shell history, but the terminal still displays what you type.

File permissions do not protect against an administrator, malware, or someone with access to your unlocked account. The database is not encrypted. Deletion requests SQLite secure deletion and removes Mirror's files, but physical erasure cannot be guaranteed on SSDs, copy-on-write filesystems, or in backups.

## Requirements

- Python 3.11 or newer.
- Zsh for automatic terminal observation. The CLI also works without shell integration.
- macOS or Linux. The letter date formatting currently requires a POSIX system.

## Install

Run this once:

```sh
git clone https://github.com/spacexbt/mirror.git && cd mirror && python3 install.py
```

The installer creates a local virtual environment, installs Mirror, initializes its memory, and adds a marked configuration block to `~/.zshrc`. It preserves existing configuration and is safe to run again after updating the repository.

Open a new terminal afterward. Mirror prints an observation whenever a new interactive Zsh starts and automatically observes commands. There is no daemon or background service to start, and you never need to run an activation command in each terminal. No command text is passed to any executable invocation in the hook.

Keep the cloned directory: the shell integration loads the program from it.

## Use

The normal commands are available in new Zsh sessions:

```sh
mirror observe   # ask for an additional observation
mirror talk      # classify one interactive message, then discard its text
mirror status    # show only aggregate counts and relationship state
mirror letter    # read the latest final letter
mirror leave     # write the final letter now and become silent
mirror forget    # confirmed, permanent deletion of ~/.mirror
```

The shell integration also requests an automatic observation every twelve recorded commands. Mirror can remain silent instead of commenting on every command.

After at least ninety days and five hundred recorded commands, a startup or automatic observation can become the final letter. Mirror then stops recording and speaking. The ending survives reinstalling the program because the local data remains. `mirror forget` is the only way to erase that state and start over.

Mirror's responses and letters use bounded templates. They can reference dates, counts, exit statuses, and pseudonymous project identifiers, but they cannot quote commands or conversations because those were never saved.

## Uninstall

Remove the entire block between `# >>> mirror >>>` and `# <<< mirror <<<` from `~/.zshrc`, then run:

```sh
/path/to/mirror/.venv/bin/python -m pip uninstall mirror-terminal
```

Uninstalling leaves local memory intact. Run `mirror forget` first if you want it deleted.

## Threat model and audit

The complete collection boundary is visible in `shell/mirror.zsh` and `src/mirror/cli.py`. The database schema in `src/mirror/storage.py` has no command-text or message-text columns. All behavior is implemented with ordinary Python rules in `src/mirror/behavior.py`; there are no hidden model or network calls.

This is a small project, not a formal security audit. Review the source before installing it, and do not treat any local application as a guarantee against a compromised operating system.

## License

MIT. See `LICENSE`.
