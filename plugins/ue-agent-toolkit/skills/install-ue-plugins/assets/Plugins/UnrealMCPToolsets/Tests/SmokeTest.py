import json
import os
import uuid

import unreal


ANIM_TOOLSET_CLASS = unreal.AnimBlueprintToolset
ANIM_TOOLSET_NAME = "UnrealMCPToolsets.AnimBlueprintToolset"
EXPECTED_ANIM_TOOLS = {
    "CreateState",
    "CreateTransition",
    "DeleteState",
    "DeleteTransition",
    "GetStateMachine",
    "ListStateMachines",
    "SetTransitionSettings",
}
PLAYTEST_TOOLSET_CLASS = unreal.PlaytestToolset
PLAYTEST_TOOLSET_NAME = "UnrealMCPToolsets.PlaytestToolset"
EXPECTED_PLAYTEST_TOOLS = {
    "InjectInputAction",
    "InjectInputActionForDuration",
    "IsInputActionInjected",
    "StartInputAction",
    "StopInputAction",
    "UpdateInputAction",
}
DEFAULT_TEST_ASSETS = (
    "/Game/Variant_Platforming/Anims/ABP_Manny_Platforming",
    "/Game/Variant_Combat/Anims/ABP_Manny_Combat",
    "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed",
    "/Game/Variant_SideScrolling/Anims/ABP_Manny_SideScroller",
)


def _asset_reference(asset):
    return {"refPath": asset.get_path_name()}


def _execute(tool_name, arguments, expected_error=None):
    result = unreal.ToolsetRegistry.execute_tool(
        ANIM_TOOLSET_NAME,
        tool_name,
        json.dumps(arguments),
    )
    assert result.is_complete, f"{tool_name} did not complete synchronously"

    if expected_error is not None:
        assert result.error, f"{tool_name} unexpectedly succeeded"
        assert expected_error in result.error, (
            f"{tool_name} returned an unclear error: {result.error}"
        )
        return None

    assert not result.error, f"{tool_name} failed: {result.error}"
    payload = json.loads(result.value)
    assert "returnValue" in payload, f"{tool_name} omitted returnValue"
    return payload["returnValue"]


def _find_test_asset():
    configured_path = os.environ.get("UNREAL_MCP_TOOLSETS_TEST_ASSET")
    candidates = (configured_path,) if configured_path else DEFAULT_TEST_ASSETS
    for asset_path in candidates:
        if asset_path and unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            return asset_path
    raise AssertionError(
        "No Animation Blueprint test asset was found. Set "
        "UNREAL_MCP_TOOLSETS_TEST_ASSET to a project asset path."
    )


def _transition_settings(crossfade_duration=0.2, priority_order=1):
    return {
        "priorityOrder": priority_order,
        "crossfadeDuration": crossfade_duration,
        "blendMode": "HermiteCubic",
        "bAutomaticRuleBasedOnSequencePlayerInState": False,
        "automaticRuleTriggerTime": -1.0,
        "minTimeBeforeReentry": -1.0,
        "bBidirectional": False,
        "bDisabled": False,
    }


def main():
    assert unreal.ToolsetRegistry.is_available(), "ToolsetRegistry is unavailable"
    assert unreal.ToolsetRegistry.is_toolset_class_registered(ANIM_TOOLSET_CLASS), (
        f"{ANIM_TOOLSET_NAME} is not registered"
    )
    assert unreal.ToolsetRegistry.is_toolset_class_registered(PLAYTEST_TOOLSET_CLASS), (
        f"{PLAYTEST_TOOLSET_NAME} is not registered"
    )

    anim_schema = json.loads(
        unreal.ToolsetRegistry.get_toolset_json_schema(ANIM_TOOLSET_CLASS)
    )
    assert anim_schema["name"] == ANIM_TOOLSET_NAME
    assert anim_schema["version"] == "0.1.0"
    exposed_anim_tools = {
        entry["name"].rsplit(".", 1)[-1] for entry in anim_schema["tools"]
    }
    assert exposed_anim_tools == EXPECTED_ANIM_TOOLS, (
        f"Unexpected Animation Blueprint tool schema: {sorted(exposed_anim_tools)}"
    )

    playtest_schema = json.loads(
        unreal.ToolsetRegistry.get_toolset_json_schema(PLAYTEST_TOOLSET_CLASS)
    )
    assert playtest_schema["name"] == PLAYTEST_TOOLSET_NAME
    assert playtest_schema["version"] == "0.1.0"
    exposed_playtest_tools = {
        entry["name"].rsplit(".", 1)[-1] for entry in playtest_schema["tools"]
    }
    assert exposed_playtest_tools == EXPECTED_PLAYTEST_TOOLS, (
        f"Unexpected playtest tool schema: {sorted(exposed_playtest_tools)}"
    )

    source_asset_path = _find_test_asset()
    source_asset = unreal.EditorAssetLibrary.load_asset(source_asset_path)
    assert source_asset is not None, f"Could not load {source_asset_path}"

    source_ref = _asset_reference(source_asset)
    state_machines = _execute("ListStateMachines", {"animBlueprint": source_ref})
    assert state_machines, f"{source_asset_path} has no state machines"
    state_machine_name = state_machines[0]["name"]
    state_machine = _execute(
        "GetStateMachine",
        {
            "animBlueprint": source_ref,
            "stateMachineName": state_machine_name,
        },
    )
    assert state_machine["name"] == state_machine_name
    _execute(
        "GetStateMachine",
        {
            "animBlueprint": source_ref,
            "stateMachineName": "__UnrealMCPToolsetsMissingMachine__",
        },
        expected_error="was not found",
    )

    run_id = uuid.uuid4().hex
    temp_directory = f"/Game/__UnrealMCPToolsetsSmoke/{run_id}"
    temp_asset_path = f"{temp_directory}/ABP_UnrealMCPToolsetsSmoke"
    temp_asset = None

    try:
        temp_asset = unreal.EditorAssetLibrary.duplicate_asset(
            source_asset_path,
            temp_asset_path,
        )
        assert temp_asset is not None, "Could not create the temporary test asset"
        temp_ref = _asset_reference(temp_asset)
        state_a = "UnrealMCPToolsets_Smoke_A"
        state_b = "UnrealMCPToolsets_Smoke_B"

        created_a = _execute(
            "CreateState",
            {
                "animBlueprint": temp_ref,
                "stateMachineName": state_machine_name,
                "stateName": state_a,
                "nodePosX": 1200,
                "nodePosY": 200,
                "bAlwaysResetOnEntry": True,
                "bCompileBlueprint": True,
                "bSaveAsset": True,
            },
        )
        assert created_a["name"] == state_a
        assert created_a["bAlwaysResetOnEntry"] is True

        created_b = _execute(
            "CreateState",
            {
                "animBlueprint": temp_ref,
                "stateMachineName": state_machine_name,
                "stateName": state_b,
                "nodePosX": 1500,
                "nodePosY": 200,
                "bCompileBlueprint": False,
                "bSaveAsset": False,
            },
        )
        assert created_b["name"] == state_b

        transition = _execute(
            "CreateTransition",
            {
                "animBlueprint": temp_ref,
                "stateMachineName": state_machine_name,
                "previousState": state_a,
                "nextState": state_b,
                "settings": _transition_settings(),
                "bCompileBlueprint": False,
                "bSaveAsset": False,
            },
        )
        assert transition["previousState"] == state_a
        assert transition["nextState"] == state_b

        updated_transition = _execute(
            "SetTransitionSettings",
            {
                "animBlueprint": temp_ref,
                "stateMachineName": state_machine_name,
                "previousState": state_a,
                "nextState": state_b,
                "settings": _transition_settings(0.35, 2),
                "bCompileBlueprint": True,
                "bSaveAsset": True,
            },
        )
        assert updated_transition["settings"]["priorityOrder"] == 2
        assert abs(updated_transition["settings"]["crossfadeDuration"] - 0.35) < 0.001

        modified_machine = _execute(
            "GetStateMachine",
            {
                "animBlueprint": temp_ref,
                "stateMachineName": state_machine_name,
            },
        )
        modified_states = {entry["name"] for entry in modified_machine["states"]}
        assert {state_a, state_b}.issubset(modified_states)
        assert any(
            entry["previousState"] == state_a and entry["nextState"] == state_b
            for entry in modified_machine["transitions"]
        )

        _execute(
            "CreateTransition",
            {
                "animBlueprint": temp_ref,
                "stateMachineName": state_machine_name,
                "previousState": state_a,
                "nextState": state_b,
                "settings": _transition_settings(-0.1),
            },
            expected_error="CrossfadeDuration must be zero or greater",
        )

        assert _execute(
            "DeleteTransition",
            {
                "animBlueprint": temp_ref,
                "stateMachineName": state_machine_name,
                "previousState": state_a,
                "nextState": state_b,
                "bCompileBlueprint": False,
                "bSaveAsset": False,
            },
        ) is True
        assert _execute(
            "DeleteState",
            {
                "animBlueprint": temp_ref,
                "stateMachineName": state_machine_name,
                "stateName": state_b,
                "bCompileBlueprint": False,
                "bSaveAsset": False,
            },
        ) is True
        assert _execute(
            "DeleteState",
            {
                "animBlueprint": temp_ref,
                "stateMachineName": state_machine_name,
                "stateName": state_a,
                "bCompileBlueprint": True,
                "bSaveAsset": True,
            },
        ) is True

        final_machine = _execute(
            "GetStateMachine",
            {
                "animBlueprint": temp_ref,
                "stateMachineName": state_machine_name,
            },
        )
        final_states = {entry["name"] for entry in final_machine["states"]}
        assert state_a not in final_states and state_b not in final_states
    finally:
        if temp_asset is not None:
            unreal.EditorAssetLibrary.delete_asset(temp_asset_path)
        unreal.EditorAssetLibrary.delete_directory(temp_directory)

    print(
        "UNREAL_MCP_TOOLSETS_SMOKE_TEST=PASS "
        f"asset={source_asset_path} state_machine={state_machine_name} "
        f"tools={len(EXPECTED_ANIM_TOOLS) + len(EXPECTED_PLAYTEST_TOOLS)}"
    )


if __name__ == "__main__":
    main()
