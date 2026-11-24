"""Package Rosavio Medien using Gecko's built-in add-on discovery."""
from pathlib import Path
from shutil import copyfile
import sys


def install(source):
    assets = Path(__file__).resolve().parent.parent / "media"
    base = source / "browser/extensions"
    target = base / "rosavio-media"
    target.mkdir(exist_ok=True)
    entries = ["browser.jar:"]
    for asset in sorted(assets.rglob("*")):
        if asset.is_file():
            relative = asset.relative_to(assets)
            dest = target / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            copyfile(asset, dest)
            entries.append(f"    builtin-addons/rosavio-media/{relative.as_posix()} ({relative.as_posix()})")
    (target / "jar.mn").write_text("\n".join(entries) + "\n", encoding="utf8")
    (target / "moz.build").write_text('JAR_MANIFESTS += ["jar.mn"]\n', encoding="utf8")
    build = base / "moz.build"
    marker = 'DIRS += ["rosavio-media"]'
    if marker not in build.read_text(encoding="utf8"):
        with build.open("a", encoding="utf8") as out:
            out.write("\n" + marker + "\n")


if __name__ == "__main__":
    install(Path(sys.argv[1]))
