import argparse
import importlib
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


def run_remote_command(engine_path, timeout_seconds, code):
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

		node = remote.remote_nodes[0]
		print('REMOTE_NODE', node)
		remote.open_command_connection(node['node_id'])

		result = remote.run_command('exec(' + repr(code) + ')', exec_mode=remote_execution.MODE_EXEC_STATEMENT)
		print('SUCCESS', result.get('success'))
		if result.get('result'):
			print('RESULT', result.get('result'))
		if result.get('output'):
			print(result.get('output'))
	finally:
		try:
			remote.close_command_connection()
		finally:
			remote.stop()


def main():
	parser = argparse.ArgumentParser(description='Read an Unreal asset as JSON through Python Remote Execution.')
	parser.add_argument('--asset-path', required=True, help='Unreal package path, object path, or recognizable asset file path.')
	parser.add_argument('--output-json', help='Output JSON path. Relative paths are resolved from the project root.')
	parser.add_argument('--engine-path', default=r'C:\EpicGames\UE_5.7', help='Unreal Engine installation path.')
	parser.add_argument('--timeout-seconds', type=int, default=10, help='Remote execution node discovery timeout.')
	parser.add_argument('--no-output-file', action='store_true', help='Print JSON only; do not write an output file.')
	parser.add_argument('--no-pretty', action='store_true', help='Disable pretty-printed JSON.')
	parser.add_argument('--include-node-properties', action='store_true', help='Include detailed Blueprint node properties.')
	args = parser.parse_args()

	os.environ['PYTHONIOENCODING'] = 'utf-8'
	project_root = find_project_root(Path(__file__).parent)
	output_json = resolve_output_json(project_root, args.asset_path, args.output_json, args.no_output_file)

	if output_json:
		Path(output_json).parent.mkdir(parents=True, exist_ok=True)

	code = "\n".join([
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
		"print('WROTE_JSON', output_json, 'LENGTH', len(result))",
	])

	run_remote_command(args.engine_path, args.timeout_seconds, code)

	if output_json and Path(output_json).exists():
		print('OUTPUT_JSON', output_json)


if __name__ == '__main__':
	main()
