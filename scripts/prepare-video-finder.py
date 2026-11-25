"""Bundle the native helper; reserve its host name for the privileged built-in add-on."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
MARKER='  lookupManifest(type, name, context) {\n    return this.init().then(() => this._lookup(type, name, context));\n  },'
PORTAL_MARKER='    if (this.portalImp) {\n      this.startupPromise = this._doInitPortalOrNMProxy()'
PORTAL_REPLACEMENT='''    // The reserved bundled helper runs INSIDE this sandbox, never on the host.
    // NativeManifests still checks the privileged built-in origin before launch.
    if (application === "org.rosavio.video_finder") this.portalImp = null;
    if (this.portalImp) {
      this.startupPromise = this._doInitPortalOrNMProxy()'''
REPLACEMENT='''  lookupManifest(type, name, context) {
    // Rosavio Video Finder: this reserved name never falls back to user/registry hosts.
    if (name === "org.rosavio.video_finder") {
      return this.init().then(async () => {
        if (type !== "stdio" || context.extension.id !== "medien@rosavio.local" ||
            !context.extension.isPrivileged ||
            context.extension.rootURI.spec !== Services.io.getProtocolHandler("resource")
              .QueryInterface(Ci.nsIResProtocolHandler)
              .resolveURI(Services.io.newURI("resource://builtin-addons/rosavio-media/"))) {
          return null;
        }
        const directory = PathUtils.join(Services.dirsvc.get("GreD", Ci.nsIFile).path, "video-finder");
        const executable = PathUtils.join(directory,
          AppConstants.platform === "win" ? "video-finder-host.exe" : "video-finder-host");
        if (!await IOUtils.exists(executable)) return null;
        const path = PathUtils.join(directory, "org.rosavio.video_finder.json");
        const manifest = await this.parseManifest(type, path, name, context, {
          name, description: "Rosavio Video Finder", type: "stdio", path: executable,
          allowed_extensions: ["medien@rosavio.local"]
        });
        return manifest ? {path, manifest} : null;
      });
    }
    return this.init().then(() => this._lookup(type, name, context));
  },'''

def install(source,bundle):
    inventory=json.loads((bundle/'bundle.json').read_text(encoding='utf-8'))
    if inventory.get('schema')!=1 or not inventory.get('qualified'):
        raise ValueError('Unqualified Video Finder helper bundle')
    for name,digest in inventory['files'].items():
        raw=bundle/name
        path=raw.resolve()
        if not path.is_relative_to(bundle.resolve()) or any(p.is_symlink() for p in (raw,*raw.parents)):
            raise ValueError('Unsafe bundle path')
        with path.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:
                raise ValueError('Video Finder bundle checksum mismatch: '+name)
    module=source/'toolkit/components/extensions/NativeManifests.sys.mjs'
    text=module.read_text(encoding='utf-8')
    messaging=source/'toolkit/components/extensions/NativeMessaging.sys.mjs'
    messaging_text=messaging.read_text(encoding='utf-8')
    if PORTAL_REPLACEMENT not in messaging_text and messaging_text.count(PORTAL_MARKER)!=1:
        raise ValueError('Upstream native portal routing changed; review required')
    if REPLACEMENT not in text:
        if text.count(MARKER)!=1:
            raise ValueError('Upstream native host lookup changed; review required')
        module.write_text(text.replace(MARKER,REPLACEMENT),encoding='utf-8',newline='\n')
    if PORTAL_REPLACEMENT not in messaging_text:
        messaging.write_text(messaging_text.replace(PORTAL_MARKER,PORTAL_REPLACEMENT),encoding='utf-8',newline='\n')
    target=source/'browser/extensions/rosavio-media/native'
    target.mkdir(parents=True,exist_ok=True)
    groups={}
    for name in sorted(inventory['files']):
        dest=target/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(bundle/name,dest)
        groups.setdefault(Path(name).parent.as_posix(),[]).append(Path(name).name)
    lines=[]
    for parent,names in groups.items():
        selector="FINAL_TARGET_FILES['video-finder']"+''.join('['+repr(part)+']' for part in Path(parent).parts if part!='.')
        values=[('native/'+(parent+'/' if parent!='.' else '')+name) for name in names]
        # mozbuild.StrictOrderingOnAppendList compares paths case-insensitively.
        values.sort(key=str.lower)
        lines.append(selector+' += '+repr(values))
    build=target.parent/'moz.build'
    text=build.read_text(encoding='utf-8').split('# Video Finder native bundle')[0].rstrip()
    build.write_text(text+'\n# Video Finder native bundle\n'+'\n'.join(lines)+'\n',encoding='utf-8')
    package=source/'browser/installer/package-manifest.in'
    text=package.read_text(encoding='utf-8')
    entry='\n[video-finder]\n@BINPATH@/video-finder/**\n'
    if '[video-finder]' not in text:
        package.write_text(text+entry,encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path)
    p.add_argument('bundle',type=Path)
    a=p.parse_args()
    install(a.source,a.bundle)
