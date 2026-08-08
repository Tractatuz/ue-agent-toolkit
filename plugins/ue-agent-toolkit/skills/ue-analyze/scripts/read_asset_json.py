import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import time


def find_project_root(start_path):
	directory = Path(start_path).resolve()
	for candidate in (directory, *directory.parents):
		if any(candidate.glob('*.uproject')):
			return candidate

	raise RuntimeError(f'Could not locate an Unreal .uproject file above: {directory}')


def find_project_file(project_root):
	project_files = list(project_root.glob('*.uproject'))
	if len(project_files) != 1:
		raise RuntimeError(f'Expected exactly one .uproject under {project_root}; found {len(project_files)}')

	return project_files[0]


def is_engine_root(path):
	return (path / 'Engine').is_dir()


def registry_engine_candidates(engine_association):
	if os.name != 'nt' or not engine_association:
		return []

	candidates = []
	try:
		import winreg
	except ImportError:
		return candidates

	try:
		with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Epic Games\Unreal Engine\Builds') as key:
			for index in range(winreg.QueryInfoKey(key)[1]):
				name, value, _ = winreg.EnumValue(key, index)
				if name == engine_association:
					candidates.append(Path(value))
	except OSError:
		pass

	for root, key_path in (
		(winreg.HKEY_LOCAL_MACHINE, rf'SOFTWARE\EpicGames\Unreal Engine\{engine_association}'),
		(winreg.HKEY_LOCAL_MACHINE, rf'SOFTWARE\WOW6432Node\EpicGames\Unreal Engine\{engine_association}'),
	):
		try:
			with winreg.OpenKey(root, key_path) as key:
				value, _ = winreg.QueryValueEx(key, 'InstalledDirectory')
				candidates.append(Path(value))
		except OSError:
			pass

	return candidates


def resolve_engine_path(project_root, engine_path):
	if engine_path:
		path = Path(engine_path).expanduser().resolve()
		if not is_engine_root(path):
			raise RuntimeError(f'Unreal Engine root was not found or invalid: {path}')
		return path

	project_file = find_project_file(project_root)
	with project_file.open('r', encoding='utf-8-sig') as handle:
		project = json.load(handle)

	engine_association = str(project.get('EngineAssociation') or '').strip()
	candidates = []
	for env_name in ('CODEX_UNREAL_ENGINE_PATH', 'UNREAL_ENGINE_PATH', 'UE_ENGINE_PATH'):
		value = os.environ.get(env_name)
		if value:
			candidates.append(Path(value))

	if engine_association:
		association_path = Path(engine_association)
		if association_path.is_absolute():
			candidates.append(association_path)

		candidates.extend(registry_engine_candidates(engine_association))
		if os.name == 'nt' and not any(separator in engine_association for separator in ('/', '\\')):
			program_files = os.environ.get('PROGRAMFILES')
			if program_files:
				candidates.append(Path(program_files) / 'Epic Games' / f'UE_{engine_association}')
			candidates.append(Path('C:/EpicGames') / f'UE_{engine_association}')

	for candidate in candidates:
		path = candidate.expanduser().resolve()
		if is_engine_root(path):
			return path

	raise RuntimeError(
		f'Could not resolve Unreal Engine path for {project_file} '
		f'(EngineAssociation={engine_association!r}). Pass --engine-path or set CODEX_UNREAL_ENGINE_PATH.'
	)


def resolve_output_json(project_root, asset_path, output_json, no_output_file):
	if no_output_file:
		return ''

	if not output_json:
		safe_name = ''.join(character if character.isalnum() or character in '_.-' else '_' for character in asset_path).strip('_')
		if not safe_name:
			safe_name = 'Asset'

		return str(project_root / 'Saved' / 'AssetToJson' / f'{safe_name}.json')

	output_path = Path(output_json)
	if not output_path.is_absolute():
		output_path = project_root / output_path

	return str(output_path)


def normalize_path_for_compare(value):
	return os.path.normcase(os.path.abspath(str(Path(value))))


def select_project_remote_node(remote_nodes, project_root):
	expected_project_root = normalize_path_for_compare(project_root)
	for node in remote_nodes:
		node_project_root = node.get('project_root')
		if node_project_root and normalize_path_for_compare(node_project_root) == expected_project_root:
			return node

	available = [
		{
			'node_id': node.get('node_id'),
			'project_name': node.get('project_name'),
			'project_root': node.get('project_root'),
			'engine_root': node.get('engine_root'),
		}
		for node in remote_nodes
	]
	raise RuntimeError(f'No Unreal remote execution node matched project root {project_root}. Available nodes: {available}')


def run_remote_command(project_root, engine_path, timeout_seconds, code):
	remote_execution_path = Path(engine_path) / 'Engine' / 'Plugins' / 'Experimental' / 'PythonScriptPlugin' / 'Content' / 'Python'
	if not remote_execution_path.exists():
		raise RuntimeError(f'Python remote_execution.py path was not found: {remote_execution_path}')

	sys.path.append(str(remote_execution_path))
	remote_execution = importlib.import_module('remote_execution')

	remote = remote_execution.RemoteExecution()
	remote.start()

	try:
		deadline = time.time() + timeout_seconds
		while not remote.remote_nodes and time.time() < deadline:
			time.sleep(0.1)

		if not remote.remote_nodes:
			raise RuntimeError('No Unreal remote execution nodes found')

		node = select_project_remote_node(remote.remote_nodes, project_root)
		print('REMOTE_NODE', node)
		remote.open_command_connection(node['node_id'])

		result = remote.run_command('exec(' + repr(code) + ')', exec_mode=remote_execution.MODE_EXEC_STATEMENT)
		print('SUCCESS', result.get('success'))
		if result.get('result'):
			print('RESULT', result.get('result'))
		if result.get('output'):
			print(result.get('output'))
		if not result.get('success'):
			raise RuntimeError('Unreal remote execution command failed')
	finally:
		try:
			remote.close_command_connection()
		finally:
			remote.stop()


def main():
	parser = argparse.ArgumentParser(description='Read an Unreal asset as JSON through Python Remote Execution.')
	parser.add_argument('--asset-path', required=True, help='Unreal package path, object path, or recognizable asset file path.')
	parser.add_argument('--output-json', help='Output JSON path. Relative paths are resolved from the project root.')
	parser.add_argument('--engine-path', help='Unreal Engine installation path. Defaults to the project EngineAssociation.')
	parser.add_argument('--timeout-seconds', type=int, default=10, help='Remote execution node discovery timeout.')
	parser.add_argument('--no-output-file', action='store_true', help='Print JSON only; do not write an output file.')
	parser.add_argument('--no-pretty', action='store_true', help='Disable pretty-printed JSON.')
	parser.add_argument('--include-node-properties', action='store_true', help='Include detailed Blueprint node properties.')
	args = parser.parse_args()

	os.environ['PYTHONIOENCODING'] = 'utf-8'
	project_root = find_project_root(Path(__file__).parent)
	engine_path = resolve_engine_path(project_root, args.engine_path)
	output_json = resolve_output_json(project_root, args.asset_path, args.output_json, args.no_output_file)

	if output_json:
		Path(output_json).parent.mkdir(parents=True, exist_ok=True)

	code = "\n".join([
		'import json',
		'import unreal',
		f'asset_path = {args.asset_path!r}',
		f'output_json = {output_json.replace(os.sep, "/")!r}',
		'result = unreal.AssetToJsonLibrary.read_asset_as_json(',
		'    asset_path,',
		'    output_json,',
		f'    {not args.no_pretty!r},',
		'    True,',
		f'    {args.include_node_properties!r},',
		')',
		'print(result)',
		'parsed = json.loads(result)',
		"if not parsed.get('ok'):",
		"    raise RuntimeError(parsed.get('error') or 'AssetToJson returned ok=false')",
		"print('WROTE_JSON', output_json, 'LENGTH', len(result))",
	])

	print('PROJECT_ROOT', project_root)
	print('ENGINE_PATH', engine_path)
	run_remote_command(project_root, engine_path, args.timeout_seconds, code)

	if output_json and Path(output_json).exists():
		print('OUTPUT_JSON', output_json)


if __name__ == '__main__':
	main()
