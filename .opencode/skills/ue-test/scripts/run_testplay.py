import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


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


def resolve_project_path(project_root, value):
	path = Path(value)
	if not path.is_absolute():
		path = project_root / path
	return path.resolve()


def make_safe_name(value):
	safe_name = ''.join(character if character.isalnum() or character in '_.-' else '_' for character in value).strip('_')
	return safe_name or 'TestPlay'


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


def resolve_result_json(project_root, spec_path, result_json):
	if result_json:
		return resolve_project_path(project_root, result_json)

	safe_name = make_safe_name(spec_path.stem)
	return project_root / 'Saved' / 'TestPlay' / 'Results' / f'{safe_name}.opencode.json'


def main():
	parser = argparse.ArgumentParser(description='Run a TestPlay PIE spec and validate the result JSON.')
	parser.add_argument('--spec-file', required=True, help='TestPlay spec JSON file. Relative paths are resolved from the project root.')
	parser.add_argument('--result-json', help='Result JSON path. Relative paths are resolved from the project root.')
	parser.add_argument('--project-file', help='Explicit .uproject path. Defaults to the only .uproject under the project root.')
	parser.add_argument('--engine-path', help='Unreal Engine installation path. Defaults to the project EngineAssociation.')
	parser.add_argument('--timeout-seconds', type=int, default=0, help='Kill UnrealEditor if it does not exit within this many seconds. 0 disables timeout.')
	parser.add_argument('--null-rhi', action='store_true', help='Pass -nullrhi to UnrealEditor.')
	parser.add_argument('--no-exit-on-complete', action='store_true', help='Do not pass -TestPlayExitOnComplete.')
	parser.add_argument('--extra-arg', action='append', default=[], help='Additional UnrealEditor argument. Repeat for multiple arguments.')
	args = parser.parse_args()

	os.environ['PYTHONIOENCODING'] = 'utf-8'
	project_root = find_project_root(Path(__file__).parent)
	project_file = resolve_project_path(project_root, args.project_file) if args.project_file else find_project_file(project_root)
	if not project_file.exists():
		raise RuntimeError(f'Project file was not found: {project_file}')

	engine_path = resolve_engine_path(project_root, args.engine_path)
	editor_exe = engine_path / 'Engine' / 'Binaries' / 'Win64' / 'UnrealEditor.exe'
	if not editor_exe.exists():
		raise RuntimeError(f'UnrealEditor.exe was not found: {editor_exe}')

	spec_path = resolve_project_path(project_root, args.spec_file)
	if not spec_path.exists():
		raise RuntimeError(f'TestPlay spec file was not found: {spec_path}')

	result_path = resolve_result_json(project_root, spec_path, args.result_json)
	result_path.parent.mkdir(parents=True, exist_ok=True)
	if result_path.exists():
		result_path.unlink()

	command = [
		str(editor_exe),
		str(project_file),
		'-unattended',
		'-nop4',
		'-nosplash',
		f'-TestPlayRun={spec_path}',
		f'-TestPlayResult={result_path}',
	]
	if not args.no_exit_on_complete:
		command.append('-TestPlayExitOnComplete')
	if args.null_rhi:
		command.append('-nullrhi')
	command.extend(args.extra_arg)

	print('PROJECT_ROOT', project_root)
	print('ENGINE_PATH', engine_path)
	print('RUN_TESTPLAY', ' '.join(command))

	try:
		completed = subprocess.run(command, timeout=args.timeout_seconds or None)
	except subprocess.TimeoutExpired:
		print('TESTPLAY_TIMEOUT', args.timeout_seconds)
		return 124

	print('EDITOR_EXIT_CODE', completed.returncode)
	if not result_path.exists():
		print('TESTPLAY_RESULT_MISSING', result_path)
		return completed.returncode or 1

	with result_path.open('r', encoding='utf-8-sig') as handle:
		result = json.load(handle)

	print('TESTPLAY_RESULT_JSON', result_path)
	print('TESTPLAY_SUCCESS', result.get('success'))
	if result.get('durationSeconds') is not None:
		print('TESTPLAY_DURATION_SECONDS', result.get('durationSeconds'))

	if not result.get('success'):
		if result.get('failedStep') is not None:
			print('TESTPLAY_FAILED_STEP', result.get('failedStep'))
		if result.get('error'):
			print('TESTPLAY_ERROR', result.get('error'))
		return 1

	return completed.returncode


if __name__ == '__main__':
	sys.exit(main())
