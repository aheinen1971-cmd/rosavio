"""Wait for a signed public deployment to reach the installed Flatpak revision."""
import time


def require_public_revision(expected, installed, update, *, phase,
                            attempts=30, interval=10, sleep=time.sleep, log=print):
    if attempts < 1:
        raise ValueError('At least one revision check required')
    for attempt in range(attempts):
        actual = installed()
        log(f'Public Flatpak {phase}: expected={expected}, installed={actual}, '
            f'check={attempt + 1}/{attempts}', flush=True)
        if actual == expected:
            return
        if attempt + 1 < attempts:
            sleep(interval)
            # Keep the real HTTPS remote and its GPG checks. Any update error,
            # including a signature failure, is fatal rather than suppressed.
            update()
    raise SystemExit(f'Wrong public Flatpak commit after bounded {phase} wait: '
                     f'expected={expected}, installed={actual}')
