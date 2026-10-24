"""Sign an unsigned Rosavio MAR using Mozilla's build-mar library and an encrypted key.

The decrypted private key stays in process memory. Native signmar verification is
still required by package-update.sh before release metadata is generated.
"""
import argparse
import configparser
import getpass
import os
import pathlib
import re
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from mardor.reader import MarReader
from mardor.writer import MarWriter

def sign_mar(source, destination, private_key, certificate, password, platform="win64"):
    if source.resolve() == destination.resolve():
        raise ValueError('Input and output must differ')
    key = serialization.load_pem_private_key(private_key.read_bytes(), password=password)
    if key.key_size != 4096:
        raise ValueError('SHA-384 MAR signing requires an RSA-4096 key')
    cert = x509.load_der_x509_certificate(certificate.read_bytes())
    public_bytes = lambda k: k.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    if public_bytes(key.public_key()) != public_bytes(cert.public_key()):
        raise ValueError('Signing key does not match the embedded update certificate')
    public_pem = cert.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    private_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    with source.open('rb') as src:
        reader = MarReader(src)
        version, channel = reader.productinfo or (None, None)
        if channel != 'rosavio-release' or not version or not re.fullmatch(r'\d+(?:\.\d+){0,3}', version):
            raise ValueError('MAR is not a stable Rosavio release')
        entries = reader.mardata.index.entries
        names = [entry.name for entry in entries]
        if len(set(names)) != len(names) or any('..' in pathlib.PurePosixPath(name).parts or name.startswith(('/', '\\')) or ':' in name for name in names):
            raise ValueError('Unsafe or duplicate MAR paths')
        layouts = {
            'win64': ('rosavio.exe', 'application.ini', 'precomplete'),
            'linux-x64': ('rosavio', 'application.ini', 'precomplete'),
            'macos-x64': ('Contents/MacOS/rosavio', 'Contents/Resources/application.ini', 'Contents/Resources/precomplete'),
            'macos-arm64': ('Contents/MacOS/rosavio', 'Contents/Resources/application.ini', 'Contents/Resources/precomplete'),
        }
        if platform not in layouts:
            raise ValueError('Unsupported update platform')
        executable, ini_path, precomplete = layouts[platform]
        required = {executable, ini_path, 'updatev3.manifest'}
        if platform != 'win64':
            required.add(precomplete)
        if not required.issubset(names):
            raise ValueError('MAR is missing required Rosavio package entries')
        ini_entry = next(entry for entry in entries if entry.name == ini_path)
        ini = configparser.ConfigParser()
        ini.read_string(b''.join(reader.extract_entry(ini_entry)).decode())
        if ini.get('App', 'Name') != 'Rosavio' or ini.get('App', 'Version') != version:
            raise ValueError('MAR application identity or version does not match')
        manifest = next(entry for entry in entries if entry.name == 'updatev3.manifest')
        if not b''.join(reader.extract_entry(manifest)).startswith(b'type "complete"'):
            raise ValueError('Only complete update MARs are supported')
        with destination.open('w+b') as dst:
            with MarWriter(dst, productversion=version, channel=channel, signing_key=private_pem, signing_algorithm='sha384') as writer:
                for entry in entries:
                    writer.add_stream(reader.extract_entry(entry, decompress=None), entry.name, compress=None, flags=entry.flags)
    with destination.open('rb') as signed:
        if not MarReader(signed).verify(public_pem):
            raise ValueError('Signed MAR did not verify')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=pathlib.Path)
    parser.add_argument('destination', type=pathlib.Path)
    parser.add_argument('private_key', type=pathlib.Path)
    parser.add_argument('certificate', type=pathlib.Path)
    parser.add_argument('--platform', choices=['win64','linux-x64','macos-x64','macos-arm64'], default='win64')
    args = parser.parse_args()
    password = (os.environ.get('ROSAVIO_SIGNING_PASSWORD') or getpass.getpass('Signing-key password: ')).encode()
    sign_mar(args.source, args.destination, args.private_key, args.certificate, password, args.platform)
    print('Rosavio MAR signed with RSA-4096 / SHA-384 and verified with the public certificate.')
