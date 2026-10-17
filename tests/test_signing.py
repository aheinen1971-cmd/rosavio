import datetime
import importlib.util
import io
import pathlib
import tempfile
import unittest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from mardor.reader import MarReader
from mardor.writer import MarWriter

script = pathlib.Path(__file__).resolve().parent.parent / 'scripts/sign-mar.py'
spec = importlib.util.spec_from_file_location('rosavio_sign_mar', script)
signer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(signer)

class SigningTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='rosavio-signing-')
        cls.root = pathlib.Path(cls.temp.name)
        cls.password = b'test-password-only-not-used-for-releases'
        key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Disposable test identity')])
        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
                .serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(days=1))
                .not_valid_after(now+datetime.timedelta(days=1)).sign(key, hashes.SHA384()))
        cls.keyfile = cls.root / 'key.pem'
        cls.certfile = cls.root / 'cert.der'
        cls.keyfile.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(cls.password)))
        cls.certfile.write_bytes(cert.public_bytes(serialization.Encoding.DER))
        cls.public = cert.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def make_unsigned(self, name, channel='rosavio-release', app='Rosavio'):
        target = self.root / name
        with target.open('w+b') as file:
            with MarWriter(file, productversion='158.0', channel=channel) as writer:
                payload = {'rosavio.exe': b'MZ-synthetic-test-fixture', 'application.ini': f'[App]\nName={app}\nVersion=158.0\n'.encode(), 'updatev3.manifest': b'type "complete"\r\nadd "rosavio.exe"\r\n'}
                for name, data in payload.items():
                    writer.add_fileobj(io.BytesIO(data), name, compress='xz', flags=0o644)
        return target

    def test_signed_mar_verifies_and_preserves_payload(self):
        source = self.make_unsigned('unsigned.mar')
        dest = self.root / 'signed.mar'
        signer.sign_mar(source, dest, self.keyfile, self.certfile, self.password)
        with source.open('rb') as src, dest.open('rb') as dst:
            left, right = MarReader(src), MarReader(dst)
            self.assertFalse(left.verify(self.public))
            self.assertTrue(right.verify(self.public))
            self.assertEqual(right.signature_type, 'sha384')
            self.assertEqual(right.productinfo, ('158.0', 'rosavio-release'))
            for a, b in zip(left.mardata.index.entries, right.mardata.index.entries):
                self.assertEqual(a.name, b.name)
                self.assertEqual(b''.join(left.extract_entry(a, decompress=None)), b''.join(right.extract_entry(b, decompress=None)))
        corrupted = bytearray(dest.read_bytes())
        with dest.open('rb') as dst:
            offset = MarReader(dst).mardata.index.entries[0].offset
        corrupted[offset + 12] ^= 1
        self.assertFalse(MarReader(io.BytesIO(corrupted)).verify(self.public))

    def test_rejects_firefox_and_wrong_channel(self):
        for index, changes in enumerate([{'app': 'Firefox'}, {'channel': 'release'}]):
            with self.assertRaises(ValueError):
                signer.sign_mar(self.make_unsigned(f'wrong-{index}.mar', **changes), self.root / f'reject-{index}.mar', self.keyfile, self.certfile, self.password)

if __name__ == '__main__':
    unittest.main()
