"""Apply process limits before executing a fixed, server-selected CSE script."""
import os
import resource
import sys

resource.setrlimit(resource.RLIMIT_CPU, (25, 26))
resource.setrlimit(resource.RLIMIT_FSIZE, (2_000_000, 2_000_000))
resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
os.execv(sys.executable, [sys.executable, '-B', *sys.argv[1:]])
