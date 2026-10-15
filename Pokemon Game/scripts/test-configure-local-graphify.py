"""Verify idempotent local setup and preservation of unrelated client settings."""
import importlib.util
import json
from pathlib import Path
import tempfile
import tomllib
import unittest

spec = importlib.util.spec_from_file_location('setup', Path(__file__).with_name('configure-local-graphify.py'))
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class ClientSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.python = self.root / 'python.exe'
        self.graph = self.root / 'graph.json'
        self.python.touch()
        self.graph.write_text('{}')
        (self.root / '.codex').mkdir()
        (self.root / '.codex/config.toml').write_text('[mcp_servers.existing]\ncommand="keep"\n')
        (self.root / '.mcp.json').write_text('{"mcpServers":{"existing":{"command":"keep"}}}')

    def test_setup_preserves_existing_servers_and_is_idempotent(self):
        setup.configure(self.root, self.python, self.graph)
        paths = [self.root / '.mcp.json', self.root / '.codex/config.toml']
        before = [path.read_bytes() for path in paths]
        setup.configure(self.root, self.python, self.graph)
        self.assertEqual(before, [path.read_bytes() for path in paths])
        self.assertEqual(json.loads(paths[0].read_text())['mcpServers']['existing'], {'command': 'keep'})
        config = tomllib.loads(paths[1].read_text())['mcp_servers']
        self.assertEqual(config['existing'], {'command': 'keep'})
        self.assertEqual(config['averon_graphify']['enabled_tools'], setup.READ_TOOLS)

    def test_conflicting_server_leaves_both_clients_untouched(self):
        path = self.root / '.codex/config.toml'
        path.write_text('[mcp_servers.averon_graphify]\ncommand="another"\n')
        before = path.read_bytes(), (self.root / '.mcp.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'differs'):
            setup.configure(self.root, self.python, self.graph)
        self.assertEqual(before, (path.read_bytes(), (self.root / '.mcp.json').read_bytes()))

    def test_missing_graph_does_not_create_a_broken_connection(self):
        with self.assertRaises(FileNotFoundError):
            setup.configure(self.root, self.python, self.root / 'missing.json')
        self.assertNotIn('averon_graphify', (self.root / '.codex/config.toml').read_text())


if __name__ == '__main__':
    unittest.main()
