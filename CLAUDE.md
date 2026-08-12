# CLAUDE.md

## General

- This is an Unreal Engine project.
- Inspect existing Unreal patterns before editing.
- Prefer the smallest correct change.
- Never revert changes without explicit user permission.
- Avoid broad refactors unless explicitly requested.

## Work Preference

- Prefer C++ changes over Blueprint or asset edits when feasible.
- Avoid modifying Blueprints, maps, or binary assets unless the task clearly requires it.
- If asset changes are necessary, call them out explicitly.

## Files

- Do not edit generated output: `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`.
- Treat `.uproject`, `.uplugin`, `.Build.cs`, and `Config/*.ini` changes as high-impact.

## C++

- Be careful with `UCLASS`, `UPROPERTY`, `UFUNCTION`, and `UENUM` renames/removals.
- Assume Blueprints or serialized assets may depend on reflected symbols.
- Follow the project's existing pointer, module, and naming style.
- Avoid gameplay logic in constructors.

## Gameplay

- Preserve networking authority and replication intent.
- Avoid adding Tick unless necessary.
- Prefer events, delegates, timers, components, or subsystems.

## Verification

- Build after C++ changes when possible.
- Explain any skipped verification.
- Call out binary asset or broad config changes explicitly.
