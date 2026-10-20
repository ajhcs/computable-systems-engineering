# Native runtime portability and installation boundary

The shared native parser needs Python 3.10+, Java and javac21+, and the same pinned
pilot archive on both Linux and Windows. This change preserves parser serialization:
POSIX uses nonblocking `flock`; Windows uses a nonblocking one-byte `msvcrt` lock
at byte zero of the same persistent `parser.lock`. A contender must wait or time
out. Lock errors never fall back to running Java without a lock. The lock file
is opened without truncation and is not deleted or replaced while contenders
may be using it. File closure and explicit release apply on parser failure too.

The existing timeout bounds lock acquisition and the Java invocation together.
Java's two-entry classpath uses the platform path separator, and source/result
pipes carry explicit UTF-8 bytes. Java launches with `-Dstdout.encoding=UTF-8`
and `-Dstderr.encoding=UTF-8`; Python strictly decodes both captured byte streams
on the calling thread. Invalid or missing streams produce a structured parser
error, including on nonzero exits. Paths with spaces remain individual subprocess
arguments; no shell command is constructed.

Run the normal required suite after installing the documented pinned parser:

```sh
python -X utf8 scripts/install_sysml_parser.py
python -X utf8 -B scripts/check.py --require-sysml
```

The new portability suite exercises real cross-process exclusion, timeout without
Java execution, release after exceptions/timeouts, preserved lock contents,
nonblocking Windows byte-zero adapter behavior, import without POSIX-only modules,
actual JVM stdout/stderr UTF-8 bytes, malformed transport errors,
and actual native acquisition of UTF-8 text in a path with spaces. The workflow
adds Windows alongside Ubuntu for both supported Python test versions. Hosted
workflow configuration alone is not a completed Windows test result; record the
actual run and revision before claiming qualification.

On Windows, Git may retain tracked `.agents/skills` symlinks as small files naming
their intended targets. The registration test checks those records, but does not
claim such a file supplies project skill discovery. Runtime tests use the real
`skills/<name>/scripts/cse.py` directory when a directory registration is absent.
Installed plugins likewise require the complete real skill directories plus the
shared scripts, verifier, reference files and qualified presentation assets.
Do not overwrite existing legacy standalone skill files or customizations to
repair a checkout. Project discovery through actual links and installed-plugin
discovery remain distinct checks.

Global installation is a separate qualification: use a clean accepted revision,
verify manifest/marketplace loading through supported clients, compare installed
payload hashes, run the installed launchers/native check, and confirm skill
discovery in a clean session. This document does not claim a marketplace install,
Windows availability, editor roundtrip or protected execution merely from local
source tests. Do not restart active sessions or replace unrelated registrations.

References: Python [msvcrt locking](https://docs.python.org/3/library/msvcrt.html),
[flock](https://docs.python.org/3/library/fcntl.html), and
[platform path separators](https://docs.python.org/3/library/os.html#os.pathsep).
