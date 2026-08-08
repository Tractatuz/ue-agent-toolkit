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


def resolve_project_path(project_root, value):
	path = Path(value)
	if not path.is_absolute():
		path = project_root / path
	return path.resolve()


def make_safe_name(value):
	safe_name = ''.join(character if character.isalnum() or character in '_.-' else '_' for character in value).strip('_')
	return safe_name or 'JsonToAsset'


def normalize_object_path(asset_path):
	asset_path = asset_path.strip()
	if asset_path.startswith('/Game/') and '.' not in asset_path:
		return f'{asset_path}.{asset_path.rsplit("/", 1)[-1]}'
	return asset_path


def load_patch_target(json_file):
	with json_file.open('r', encoding='utf-8-sig') as handle:
		root = json.load(handle)

	if not isinstance(root, dict):
		raise RuntimeError('Patch JSON root must be an object')

	asset = root.get('asset')
	if not isinstance(asset, dict):
		raise RuntimeError('Patch JSON must contain an asset object')

	asset_path = asset.get('object_path') or asset.get('path')
	if not isinstance(asset_path, str) or not asset_path.strip():
		raise RuntimeError('Patch JSON asset.object_path or asset.path must be a non-empty string')

	return normalize_object_path(asset_path)


def resolve_result_json(project_root, json_file, result_json):
	if result_json:
		return resolve_project_path(project_root, result_json)

	safe_name = make_safe_name(json_file.stem)
	return project_root / 'Saved' / 'JsonToAsset' / f'{safe_name}.result.json'


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


def build_editor_code(args, json_file, result_json, target_object_path):
	json_file_text = str(json_file).replace(os.sep, '/')
	result_json_text = str(result_json).replace(os.sep, '/')

	return "\n".join([
		'import json',
		'import os',
		'import unreal',
		'',
		f'json_file = {json_file_text!r}',
		f'result_json = {result_json_text!r}',
		f'target_object_path = {target_object_path!r}',
		f'create_missing_blueprint = {args.create_missing_blueprint!r}',
		f'parent_class_path = {args.parent_class!r}',
		f'save_asset = {not args.no_save!r}',
		f'compile_blueprint = {not args.no_compile!r}',
		f'apply_graph_changes = {not args.no_graph_changes!r}',
		f'allow_structural_changes = {args.allow_structural_changes!r}',
		'',
		'def write_result(result):',
		'    if result_json:',
		'        os.makedirs(os.path.dirname(result_json), exist_ok=True)',
		"        with open(result_json, 'w', encoding='utf-8') as handle:",
		'            handle.write(result)',
		'',
		'def package_path_from_object_path(object_path):',
		"    return object_path.split('.', 1)[0] if '.' in object_path else object_path",
		'',
		'def create_blueprint_if_missing():',
		'    existing = unreal.load_asset(target_object_path)',
		'    if existing:',
		"        print('BLUEPRINT_EXISTS', target_object_path)",
		'        return',
		'',
		'    package_path = package_path_from_object_path(target_object_path)',
		"    if not package_path.startswith('/Game/') or '/' not in package_path[6:]:",
		"        raise RuntimeError('Can only create project Blueprint assets under /Game/<Folder>/<AssetName>: ' + package_path)",
		'',
		"    asset_name = package_path.rsplit('/', 1)[-1]",
		"    asset_folder = package_path.rsplit('/', 1)[0]",
		'    parent_class = unreal.load_class(None, parent_class_path)',
		'    if not parent_class:',
		"        raise RuntimeError('Failed to load parent class: ' + parent_class_path)",
		'',
		'    factory = unreal.BlueprintFactory()',
		"    factory.set_editor_property('ParentClass', parent_class)",
		'    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()',
		'    blueprint = asset_tools.create_asset(asset_name, asset_folder, unreal.Blueprint, factory)',
		'    if not blueprint:',
		"        raise RuntimeError('Failed to create Blueprint asset: ' + package_path)",
		'',
		"    print('CREATED_BLUEPRINT', blueprint.get_path_name())",
		'    if save_asset:',
		'        if hasattr(unreal, \'EditorAssetLibrary\'):',
		'            unreal.EditorAssetLibrary.save_loaded_asset(blueprint)',
		'        else:',
		'            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)',
		'',
		'if create_missing_blueprint:',
		'    create_blueprint_if_missing()',
		'',
		'result = unreal.JsonToAssetLibrary.apply_blueprint_visual_script_json_file(',
		'    json_file,',
		'    save_asset,',
		'    compile_blueprint,',
		'    apply_graph_changes,',
		'    allow_structural_changes,',
		')',
		'write_result(result)',
		"print('JSON_TO_ASSET_RESULT', result)",
		'',
		'parsed = json.loads(result)',
		"if not parsed.get('ok'):",
		"    raise RuntimeError(parsed.get('error') or 'JsonToAsset returned ok=false')",
	])


def main():
	parser = argparse.ArgumentParser(description='Apply a JsonToAsset Blueprint patch through Unreal Python Remote Execution.')
	parser.add_argument('--json-file', required=True, help='JsonToAsset patch JSON file. Relative paths are resolved from the project root.')
	parser.add_argument('--result-json', help='Result JSON path. Relative paths are resolved from the project root.')
	parser.add_argument('--engine-path', help='Unreal Engine installation path. Defaults to the project EngineAssociation.')
	parser.add_argument('--timeout-seconds', type=int, default=10, help='Remote execution node discovery timeout.')
	parser.add_argument('--create-missing-blueprint', action='store_true', help='Create a missing Blueprint asset before applying the patch.')
	parser.add_argument('--parent-class', default='/Script/Engine.Actor', help='Parent class path for --create-missing-blueprint.')
	parser.add_argument('--no-save', action='store_true', help='Apply changes without saving the asset package.')
	parser.add_argument('--no-compile', action='store_true', help='Apply changes without compiling the Blueprint.')
	parser.add_argument('--no-graph-changes', action='store_true', help='Skip graph node, pin, and link patching.')
	parser.add_argument('--allow-structural-changes', action='store_true', help='Pass through JsonToAsset structural-change opt-in. Current plugin may warn if unsupported.')
	parser.add_argument('--validate-json-only', action='store_true', help='Validate local patch JSON and target path without contacting Unreal.')
	args = parser.parse_args()

	os.environ['PYTHONIOENCODING'] = 'utf-8'
	project_root = find_project_root(Path(__file__).parent)
	engine_path = resolve_engine_path(project_root, args.engine_path)
	json_file = resolve_project_path(project_root, args.json_file)
	if not json_file.exists():
		raise RuntimeError(f'Patch JSON file does not exist: {json_file}')

	target_object_path = load_patch_target(json_file)
	result_json = resolve_result_json(project_root, json_file, args.result_json)

	print('PROJECT_ROOT', project_root)
	print('ENGINE_PATH', engine_path)
	print('PATCH_JSON', json_file)
	print('TARGET_OBJECT_PATH', target_object_path)
	print('RESULT_JSON', result_json)

	if args.validate_json_only:
		print('VALID_JSON true')
		return

	result_json.parent.mkdir(parents=True, exist_ok=True)

	code = build_editor_code(args, json_file, result_json, target_object_path)
	run_remote_command(project_root, engine_path, args.timeout_seconds, code)

	if result_json.exists():
		print('OUTPUT_JSON', result_json)
		with result_json.open('r', encoding='utf-8-sig') as handle:
			result = json.load(handle)

		print('JSON_TO_ASSET_OK', result.get('ok'))
		print('JSON_TO_ASSET_CHANGE_COUNT', result.get('change_count'))
		print('JSON_TO_ASSET_WARNING_COUNT', result.get('warning_count'))
		if not result.get('ok'):
			raise RuntimeError(result.get('error') or 'JsonToAsset returned ok=false')


if __name__ == '__main__':
	main()
