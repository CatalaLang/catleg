"""
Interface to git's word-level diff (git diff --color-word).
Requires a system install of git.
"""
import tempfile
from subprocess import run


def wdiff(st1: str, st2: str):
    """
    Draft implementation. Has issues:
      - why does git diff exit with a nonzero code? (currently bypassing with check=False...)
      - use proper file names and line info
    """
    with tempfile.NamedTemporaryFile(mode="w") as sf1, tempfile.NamedTemporaryFile(
        mode="w"
    ) as sf2:
        sf1.write(st1)
        sf2.write(st2)
        sf1.flush()
        sf2.flush()
        result = run(
            ["git", "diff", "--no-index", "--color-words", sf1.name, sf2.name],
            check=False,
        )
        return result.stdout
