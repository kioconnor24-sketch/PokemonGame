"""Create local-only MCP client configs without replacing existing connections."""
import argparse
import json
from pathlib import Path
import tomllib


READ_TOOLS = ['query_graph', 'get_node', 'get_neighbors', 'shortest_path', 'graph_stats']


def configure(repository, python, graph):
    repository, python, graph = (Path(p).resolve(strict=True) for p in (repository, python, graph))
    claude_path = repository / '.mcp.json'
    codex_path = repository / '.codex/config.toml'
    server = {'command': str(python), 'args': ['-m', 'graphify.serve', str(graph)]}
    claude = json.loads(claude_path.read_text(encoding='utf-8')) if claude_path.exists() else {}
    servers = claude.setdefault('mcpServers', {})
    if 'averon_graphify' in servers and servers['averon_graphify'] != server:
        raise ValueError('Existing Claude averon_graphify differs; no configuration written')
    old = codex_path.read_text(encoding='utf-8') if codex_path.exists() else ''
    parsed = tomllib.loads(old)
    current = parsed.get('mcp_servers', {}).get('averon_graphify')
    codex_server = dict(server, enabled_tools=READ_TOOLS, default_tools_approval_mode='writes')
    if current is not None and current != codex_server:
        raise ValueError('Existing Codex averon_graphify differs; no configuration written')
    # Both configurations have been checked before any write. Never change trust,
    # permission bypasses, existing servers, account connections or lifecycle hooks.
    servers['averon_graphify'] = server
    codex_path.parent.mkdir(parents=True, exist_ok=True)
    if current is None:
        fields = '\n'.join(f'{key} = {json.dumps(value)}' for key, value in codex_server.items())
        codex_path.write_text(old.rstrip() + '\n\n[mcp_servers.averon_graphify]\n' + fields + '\n', encoding='utf-8')
    claude_path.write_text(json.dumps(claude, indent=2) + '\n', encoding='utf-8')
    return {'repository': str(repository), 'configured': ['Claude project MCP', 'Codex project MCP'],
            'transport': 'local stdio', 'client_connection': 'pending client reload/approval'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--python', required=True)
    parser.add_argument('--graph', required=True)
    args = parser.parse_args()
    print(json.dumps(configure(args.repository, args.python, args.graph), indent=2))
