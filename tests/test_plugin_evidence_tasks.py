"""Task interfaces preserve native result transport and keep policy out of collectors."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]

class PluginEvidenceTasks(unittest.TestCase):
    def task(self, name):
        return yaml.safe_load((ROOT / 'task' / name / f'{name}.yaml').read_text())['spec']

    def test_prepare_declares_inventory_for_chains(self):
        results = {r['name']: r for r in self.task('prepare-plugin-oci-ta')['results']}
        self.assertEqual(results['PLUGIN_PACKAGE']['type'], 'string')
        self.assertEqual(results['SKILLS']['type'], 'array')

    def test_collectors_use_trusted_source_and_explicit_evidence_results(self):
        for name, result in [('verify-plugin-evidence','PLUGIN_VERIFICATION'),('collect-plugin-context','COMPASS_CONTEXT')]:
            task = self.task(name)
            self.assertEqual({r['name'] for r in task['results']}, {result,'TEST_OUTPUT'})
            self.assertEqual(task['steps'][0]['args'], ['use','$(params.SOURCE_ARTIFACT)=/var/workdir/source'])
            self.assertIn('@sha256:',task['steps'][0]['image'])
            self.assertEqual(task['steps'][1]['command'], ['python','-m','src.component'])
            self.assertFalse(any(p['name'] in {'market','threshold','requirements'} for p in task['params']))

    def test_compass_uses_verified_native_ca_without_directory_override(self):
        task = self.task('collect-plugin-context')
        env = {e['name']:e for e in task['stepTemplate']['env']}
        self.assertIn('SSL_CERT_FILE',env)
        self.assertNotIn('SSL_CERT_DIR',env)
        self.assertNotIn('insecure-ssl', {p['name'] for p in task['params']})
