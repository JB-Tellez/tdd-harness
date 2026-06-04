# Skills

A collection of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) you can install individually. Each top-level directory is a self-contained skill — install only the ones you want.

## Available skills

| Skill | What it does |
| --- | --- |
| [`auto-tdd`](./auto-tdd/SKILL.md) | Autonomous variant of `tdd` — agent plays both implementer and a simulated developer (via subagents) at every gate, so a feature can be driven end-to-end without mid-cycle human approvals. |
| [`deglaze`](./deglaze/SKILL.md) | Pre-commit engagement check — asks you to explain changes in your own words before committing. |
| [`tdd`](./tdd/SKILL.md) | Implements a feature or fix using strict Test-Driven Development (red-green-refactor). |

Open a skill's `SKILL.md` to see its full behavior before installing.

## Picking a skill

Each skill is a directory containing a `SKILL.md` file with frontmatter describing its purpose. To evaluate a skill:

1. Read the `description` field at the top of its `SKILL.md`. Claude uses this string to decide when to trigger the skill.
2. Skim the body for the process, inputs, and outputs.
3. Install the skills whose descriptions match workflows you want Claude to use.

## Installing

Skills live in one of two locations:

- **User-level** (`~/.claude/skills/`) — available in every project on your machine.
- **Project-level** (`.claude/skills/` inside a repo) — scoped to that repo, and checked in for your team.

The install step is the same either way: copy or symlink the skill's directory into the target `skills/` folder. Symlinking is recommended so `git pull` in this repo updates your installed skills automatically.

### Install one skill (user-level, symlink)

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/deglaze" ~/.claude/skills/deglaze
```

### Install one skill (project-level, copy)

From the target project's root:

```bash
mkdir -p .claude/skills
cp -R /path/to/this/repo/tdd .claude/skills/tdd
```

### Install several at once

```bash
for skill in deglaze tdd; do
  ln -s "$(pwd)/$skill" ~/.claude/skills/$skill
done
```

### Verify

Start (or restart) Claude Code in a project and run `/help`, or type `/` to see the skill appear in the command list. You can also ask Claude "what skills do you have available?"

## Using a skill

Once installed, invoke a skill by typing `/<skill-name>` in Claude Code — for example `/deglaze` or `/tdd add email validation`. Claude may also trigger a skill automatically when your request matches its description.

## Uninstalling

Remove the symlink or directory:

```bash
rm ~/.claude/skills/deglaze
# or for a copied skill:
rm -rf .claude/skills/tdd
```

## Contributing a skill

1. Create a new top-level directory named after your skill (lowercase, hyphen-separated).
2. Add a `SKILL.md` with frontmatter:
   ```markdown
   ---
   name: your-skill
   description: One-line trigger hint — Claude reads this to decide when to use the skill.
   ---
   ```
3. Document the process in the body: what it does, when to run it, and the exact steps Claude should follow.
4. Open a merge request.

Keep skills focused — one workflow per skill. If it needs several modes, consider splitting it.
