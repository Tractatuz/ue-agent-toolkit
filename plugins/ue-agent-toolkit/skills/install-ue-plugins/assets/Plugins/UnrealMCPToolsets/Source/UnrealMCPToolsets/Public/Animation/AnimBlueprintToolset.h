#pragma once

#include "AlphaBlend.h"
#include "CoreMinimal.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "AnimBlueprintToolset.generated.h"

class UAnimBlueprint;

USTRUCT(BlueprintType)
struct FAnimBlueprintToolsetStateInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString Name;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString NodeId;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString BoundGraphPath;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString StateType;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	int32 NodePosX = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	int32 NodePosY = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	bool bAlwaysResetOnEntry = false;
};

USTRUCT(BlueprintType)
struct FAnimBlueprintToolsetTransitionSettings
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anim Blueprint")
	int32 PriorityOrder = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anim Blueprint")
	float CrossfadeDuration = 0.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anim Blueprint")
	EAlphaBlendOption BlendMode = EAlphaBlendOption::HermiteCubic;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anim Blueprint")
	bool bAutomaticRuleBasedOnSequencePlayerInState = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anim Blueprint")
	float AutomaticRuleTriggerTime = -1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anim Blueprint")
	float MinTimeBeforeReentry = -1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anim Blueprint")
	bool bBidirectional = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anim Blueprint")
	bool bDisabled = false;
};

USTRUCT(BlueprintType)
struct FAnimBlueprintToolsetTransitionInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString NodeId;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString PreviousState;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString NextState;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString BoundGraphPath;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString CustomTransitionGraphPath;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FAnimBlueprintToolsetTransitionSettings Settings;
};

USTRUCT(BlueprintType)
struct FAnimBlueprintToolsetStateMachineSummary
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString Name;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString GraphPath;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString OwnerNodePath;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	int32 StateCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	int32 TransitionCount = 0;
};

USTRUCT(BlueprintType)
struct FAnimBlueprintToolsetStateMachineInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString AnimBlueprintPath;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString Name;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString GraphPath;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString OwnerNodePath;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	FString EntryState;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	TArray<FAnimBlueprintToolsetStateInfo> States;

	UPROPERTY(BlueprintReadOnly, Category = "Anim Blueprint")
	TArray<FAnimBlueprintToolsetTransitionInfo> Transitions;
};

/**
 * MCP tools for inspecting and editing existing Animation Blueprint state machines.
 * General Blueprint graph editing is intentionally left to the standard Blueprint toolsets.
 */
UCLASS(BlueprintType)
class UNREALMCPTOOLSETS_API UAnimBlueprintToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	virtual FString GetToolsetVersion() const override
	{
		return TEXT("0.1.0");
	}

	/**
	 * Lists every state machine owned by an Animation Blueprint.
	 *
	 * @param AnimBlueprint Animation Blueprint asset to inspect.
	 * @return State machine names, paths, and state/transition counts.
	 */
	UFUNCTION(meta = (AICallable), Category = "AnimBlueprint|StateMachine")
	static TArray<FAnimBlueprintToolsetStateMachineSummary> ListStateMachines(const UAnimBlueprint* AnimBlueprint);

	/**
	 * Returns states, transitions, entry state, and transition settings for one state machine.
	 *
	 * @param AnimBlueprint Animation Blueprint asset to inspect.
	 * @param StateMachineName Exact state machine name returned by ListStateMachines.
	 */
	UFUNCTION(meta = (AICallable), Category = "AnimBlueprint|StateMachine")
	static FAnimBlueprintToolsetStateMachineInfo GetStateMachine(
		const UAnimBlueprint* AnimBlueprint,
		const FString& StateMachineName);

	/**
	 * Creates a normal animation state in an existing state machine.
	 *
	 * @param AnimBlueprint Animation Blueprint asset to modify.
	 * @param StateMachineName State machine that will own the state.
	 * @param StateName Unique state name.
	 * @param NodePosX Horizontal graph position.
	 * @param NodePosY Vertical graph position.
	 * @param bAlwaysResetOnEntry Whether the state always resets when re-entered.
	 * @param bCompileBlueprint Compile after the change.
	 * @param bSaveAsset Save the package after the change.
	 * @return Information about the created state.
	 */
	UFUNCTION(meta = (AICallable), Category = "AnimBlueprint|StateMachine")
	static FAnimBlueprintToolsetStateInfo CreateState(
		UAnimBlueprint* AnimBlueprint,
		const FString& StateMachineName,
		const FString& StateName,
		int32 NodePosX = 0,
		int32 NodePosY = 0,
		bool bAlwaysResetOnEntry = false,
		bool bCompileBlueprint = true,
		bool bSaveAsset = false);

	/**
	 * Deletes a normal animation state and every transition connected to it.
	 */
	UFUNCTION(meta = (AICallable), Category = "AnimBlueprint|StateMachine")
	static bool DeleteState(
		UAnimBlueprint* AnimBlueprint,
		const FString& StateMachineName,
		const FString& StateName,
		bool bCompileBlueprint = true,
		bool bSaveAsset = false);

	/**
	 * Creates a directed transition between two normal animation states.
	 *
	 * @param Settings Complete initial settings for the transition.
	 * @return Information about the created transition.
	 */
	UFUNCTION(meta = (AICallable), Category = "AnimBlueprint|StateMachine")
	static FAnimBlueprintToolsetTransitionInfo CreateTransition(
		UAnimBlueprint* AnimBlueprint,
		const FString& StateMachineName,
		const FString& PreviousState,
		const FString& NextState,
		const FAnimBlueprintToolsetTransitionSettings& Settings,
		bool bCompileBlueprint = true,
		bool bSaveAsset = false);

	/**
	 * Deletes the directed transition from PreviousState to NextState.
	 */
	UFUNCTION(meta = (AICallable), Category = "AnimBlueprint|StateMachine")
	static bool DeleteTransition(
		UAnimBlueprint* AnimBlueprint,
		const FString& StateMachineName,
		const FString& PreviousState,
		const FString& NextState,
		bool bCompileBlueprint = true,
		bool bSaveAsset = false);

	/**
	 * Replaces the editable settings of an existing directed transition.
	 *
	 * @param Settings Complete replacement settings. Query GetStateMachine first when only
	 * one field should change so the other values can be preserved.
	 * @return Updated transition information.
	 */
	UFUNCTION(meta = (AICallable), Category = "AnimBlueprint|StateMachine")
	static FAnimBlueprintToolsetTransitionInfo SetTransitionSettings(
		UAnimBlueprint* AnimBlueprint,
		const FString& StateMachineName,
		const FString& PreviousState,
		const FString& NextState,
		const FAnimBlueprintToolsetTransitionSettings& Settings,
		bool bCompileBlueprint = true,
		bool bSaveAsset = false);
};
