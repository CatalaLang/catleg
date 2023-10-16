"""
Interface to git's word-level diff (git diff --color-word).
Requires a system install of git.
"""
import tempfile
from subprocess import run


def wdiff(st1: str, st2: str, *, return_exit_code=False, line_offset=0):
    """
    Interface to git's word-level diff.
    """
    with tempfile.NamedTemporaryFile(mode="w") as sf1, tempfile.NamedTemporaryFile(
        mode="w"
    ) as sf2:
        sf1.write("\n" * line_offset)
        sf1.write(st1)
        sf2.write("\n" * line_offset)
        sf2.write(st2)
        sf1.flush()
        sf2.flush()
        result = run(
            [
                "git",
                "--no-pager",
                "diff",
                "--ignore-space-at-eol",
                "--no-index",
                "--exit-code",
                "--color-words",
                sf1.name,
                sf2.name,
            ],
            capture_output=True,
            check=False,
        )
        output = b"\n".join(result.stdout.splitlines()[4:])
        if return_exit_code:
            return output, result.returncode
        else:
            return output
