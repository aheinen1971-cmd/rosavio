"""Create Rosavio's private MAR signing identity outside the distributable project."""
import argparse
import datetime
import getpass
import os
import pathlib
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

parser = argparse.ArgumentParser()
parser.add_argument('--private-dir', type=pathlib.Path, required=True)
parser.add_argument('--public-dir', type=pathlib.Path, required=True)
args = parser.parse_args()
private = args.private_dir.resolve()
public = args.public_dir.resolve()
private.mkdir(parents=True, exist_ok=True)
public.mkdir(parents=True, exist_ok=True)
if (private / 'rosavio-update-key.pem').exists():
    raise SystemExit('Refusing to overwrite an existing update key')
password = (os.environ.get('ROSAVIO_SIGNING_PASSWORD') or getpass.getpass('Signing-key password: ')).encode()
if len(password) < 20:
    raise SystemExit('Use a password with at least 20 characters')
key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Rosavio Update Signing')])
now = datetime.datetime.now(datetime.timezone.utc)
cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False, key_encipherment=False,
            data_encipherment=False, key_agreement=False, key_cert_sign=False, crl_sign=False,
            encipher_only=False, decipher_only=False), critical=True).sign(key, hashes.SHA384()))
(private / 'rosavio-update-key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(password)))
(private / 'rosavio-update-signing.p12').write_bytes(pkcs12.serialize_key_and_certificates(b'rosavio-update', key, cert, None, serialization.BestAvailableEncryption(password)))
(public / 'rosavio-update.der').write_bytes(cert.public_bytes(serialization.Encoding.DER))
print('Created encrypted private update identity and public certificate. Keep the private directory backed up separately.')
