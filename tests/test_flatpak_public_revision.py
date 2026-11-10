import pathlib,subprocess,sys,unittest
from unittest.mock import Mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from flatpak_public_revision import require_public_revision


class PublicRevisionTests(unittest.TestCase):
    def check(self, values, update=None, phase='seed', attempts=3):
        installed=Mock(side_effect=values); update=update or Mock()
        sleep=Mock(); log=Mock()
        require_public_revision('expected',installed,update,phase=phase,
                                attempts=attempts,interval=10,sleep=sleep,log=log)
        return installed,update,sleep,log

    def test_matching_baseline_does_not_update(self):
        _,update,sleep,_=self.check(['expected'])
        update.assert_not_called();sleep.assert_not_called()

    def test_delayed_baseline_requires_exact_revision(self):
        installed,update,sleep,log=self.check(['previous','previous','expected'])
        self.assertEqual(installed.call_count,3)
        self.assertEqual(update.call_count,2);self.assertEqual(sleep.call_count,2)
        self.assertIn('installed=previous',log.call_args_list[0].args[0])

    def test_delayed_candidate(self):
        _,update,_,_=self.check(['baseline','expected'],phase='verify')
        update.assert_called_once()

    def test_wrong_revision_never_passes(self):
        with self.assertRaisesRegex(SystemExit,'expected=expected, installed=wrong'):
            self.check(['wrong']*3)

    def test_signature_or_transport_failure_is_not_swallowed(self):
        update=Mock(side_effect=subprocess.CalledProcessError(1,['flatpak','update']))
        with self.assertRaises(subprocess.CalledProcessError):
            self.check(['previous'],update)
        update.assert_called_once()

    def test_no_checks_rejected(self):
        with self.assertRaises(ValueError):self.check([],attempts=0)


if __name__=='__main__':unittest.main()
