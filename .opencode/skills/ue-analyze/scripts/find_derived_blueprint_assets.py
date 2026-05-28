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
	for env_name in ('OPENCODE_UNREAL_ENGINE_PATH', 'UNREAL_ENGINE_PATH', 'UE_ENGINE_PATH'):
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
		f'(EngineAssociation={engine_association!r}). Pass --engine-path or set OPENCODE_UNREAL_ENGINE_PATH.'
	)


def make_safe_name(value, fallback):
	safe_name = ''.join(character if character.isalnum() or character in '_.-' else '_' for character in value).strip('_')
	return safe_name or fallback


def resolve_output_json(project_root, class_path, output_json, no_output_file):
	if no_output_file:
		return ''

	if not output_json:
		safe_name = make_safe_name(class_path, 'Class')
		return str(project_root / 'Saved' / 'AssetToJson' / f'DerivedBlueprints_{safe_name}.json')

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
	parser = argparse.ArgumentParser(description='Find Blueprint assets derived from an Unreal class through Python Remote Execution.')
	parser.add_argument('--class-path', required=True, help='Parent class path, usually /Script/<Module>.<ClassName>.')
	parser.add_argument('--output-json', help='Output JSON path. Relative paths are resolved from the project root.')
	parser.add_argument('--search-paths', nargs='+', default=['/Game'], help='Content roots to scan.')
	parser.add_argument('--engine-path', help='Unreal Engine installation path. Defaults to the project EngineAssociation.')
	parser.add_argument('--timeout-seconds', type=int, default=10, help='Remote execution node discovery timeout.')
	parser.add_argument('--no-output-file', action='store_true', help='Print JSON only; do not write an output file.')
	parser.add_argument('--no-pretty', action='store_true', help='Disable pretty-printed JSON.')
	parser.add_argument('--direct-only', action='store_true', help='Include only Blueprints whose immediate parent is the target class.')
	args = parser.parse_args()

	os.environ['PYTHONIOENCODING'] = 'utf-8'
	project_root = find_project_root(Path(__file__).parent)
	engine_path = resolve_engine_path(project_root, args.engine_path)
	output_json = resolve_output_json(project_root, args.class_path, args.output_json, args.no_output_file)

	if output_json:
		Path(output_json).parent.mkdir(parents=True, exist_ok=True)

	payload = {
		'class_path': args.class_path,
		'output_json': output_json.replace(os.sep, '/') if output_json else '',
		'pretty': not args.no_pretty,
		'direct_only': args.direct_only,
		'search_paths': args.search_paths,
	}

	code = 'import json\n_payload = json.loads(' + repr(json.dumps(payload)) + ')\n' + r'''
import os
import unreal

class_path = _payload['class_path']
output_json = _payload['output_json']
pretty = _payload['pretty']
direct_only = _payload['direct_only']
search_paths = _payload['search_paths']

def object_path(obj):
    return obj.get_path_name() if obj else ''

def make_error(message):
    return {
        'schema': 'ue.analysis.derived_blueprints.v1',
        'ok': False,
        'error': message,
        'target_class': class_path,
        'search_paths': search_paths,
        'assets': [],
    }

target_class = unreal.load_class(None, class_path)
if not target_class:
    result = make_error('Class could not be loaded: ' + class_path)
else:
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    matched_assets = []
    scanned_asset_count = 0
    loaded_blueprint_count = 0
    warnings = []
    blueprint_records = []
    target_class_path = object_path(target_class)
    target_class_asset_path = unreal.SystemLibrary.get_class_top_level_asset_path(target_class)
    derived_class_paths = set()

    def normalize_class_tag(value):
        if not value:
            return ''

        text = str(value)
        if "'" in text:
            text = text.split("'", 1)[1].rsplit("'", 1)[0]

        return text

    def top_level_asset_path_to_string(value):
        return str(value.package_name) + '.' + str(value.asset_name)

    for derived_asset_data in unreal.AssetRegistryHelpers.get_derived_class_asset_data([target_class_asset_path]):
        derived_class_path = normalize_class_tag(derived_asset_data.get_tag_value('GeneratedClass'))
        if derived_class_path:
            derived_class_paths.add(derived_class_path)

    for search_path in search_paths:
        try:
            asset_data_list = asset_registry.get_assets_by_path(search_path, recursive=True)
        except TypeError:
            asset_data_list = asset_registry.get_assets_by_path(search_path, True)

        for asset_data in asset_data_list:
            scanned_asset_count += 1

            generated_class_path = normalize_class_tag(asset_data.get_tag_value('GeneratedClass'))
            if not generated_class_path:
                continue

            parent_class_path = normalize_class_tag(asset_data.get_tag_value('ParentClass'))
            if not parent_class_path:
                parent_class_path = normalize_class_tag(asset_data.get_tag_value('NativeParentClass'))

            if not parent_class_path:
                warnings.append('Blueprint asset has no parent class tag: {0}'.format(asset_data.package_name))
                continue

            loaded_blueprint_count += 1
            object_path_string = str(asset_data.package_name) + '.' + str(asset_data.asset_name)
            blueprint_records.append({
                'path': str(asset_data.package_name),
                'object_path': object_path_string,
                'name': str(asset_data.asset_name),
                'class': top_level_asset_path_to_string(asset_data.asset_class_path),
                'parent_class': parent_class_path,
                'generated_class': generated_class_path,
            })

    for record in blueprint_records:
        is_direct_child = record['parent_class'] == target_class_path
        if direct_only:
            b_matches = is_direct_child
        else:
            b_matches = is_direct_child or record['generated_class'] in derived_class_paths

        if not b_matches:
            continue

        matched_assets.append({
            'path': record['path'],
            'object_path': record['object_path'],
            'name': record['name'],
            'class': record['class'],
            'parent_class': record['parent_class'],
            'generated_class': record['generated_class'],
            'is_direct_child': is_direct_child,
        })

    matched_assets.sort(key=lambda item: item.get('path', ''))
    result = {
        'schema': 'ue.analysis.derived_blueprints.v1',
        'ok': True,
        'target_class': target_class_path,
        'search_paths': search_paths,
        'direct_only': direct_only,
        'scanned_asset_count': scanned_asset_count,
        'loaded_blueprint_count': loaded_blueprint_count,
        'match_count': len(matched_assets),
        'assets': matched_assets,
        'warnings': warnings,
    }

json_text = json.dumps(result, indent=2 if pretty else None, ensure_ascii=False)

if output_json:
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as output_file:
        output_file.write(json_text)

print(json_text)
if not result.get('ok'):
    raise RuntimeError(result.get('error') or 'Derived Blueprint discovery returned ok=false')
print('WROTE_JSON', output_json, 'LENGTH', len(json_text))
'''

	print('PROJECT_ROOT', project_root)
	print('ENGINE_PATH', engine_path)
	run_remote_command(project_root, engine_path, args.timeout_seconds, code)

	if output_json and Path(output_json).exists():
		print('OUTPUT_JSON', output_json)


if __name__ == '__main__':
	main()
