# Setup (for Claude)

The person has just opened this folder in Claude Code for the first time. Get their computer ready to render videos, then stop.

1. Run the checker from the skill folder on this folder:
   - Windows: `python .claude/skills/engineering-failures-video/scripts/check.py .`
   - Mac/Linux: `python3 .claude/skills/engineering-failures-video/scripts/check.py .`
   If Python itself is missing, install it first (Windows: `winget install -e --id Python.Python.3.12`; Mac: the installer from python.org).
2. For every line marked MISSING, install it using the command the checker prints. Ask before each install, and explain in one short sentence what it is for. If the person says not to use Homebrew, use the official installers or static builds described in the skill's `reference/production.md`. Word timing (faster-whisper) is needed later, so install it now too; if it fails, follow "Word timing install fallback" in `reference/production.md`.
3. If "HyperFrames + GSAP" is MISSING, install it once for all episodes with `python .claude/skills/engineering-failures-video/scripts/setup.py . --toolchain-only` (`python3` on Mac).
4. If anything new was installed, tell the person to quit and reopen Claude, open this same folder in the Code tab, and say "Follow SETUP.md" again.
5. When every line is OK, reply with one short message: "You're set up. Tell me what to make, for example: Make a documentary about the Baltimore Key Bridge collapse." Do not render any test video.
