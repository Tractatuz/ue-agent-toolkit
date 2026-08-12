#include "Animation/AnimBlueprintToolset.h"

#include "Animation/AnimBlueprint.h"
#include "AnimationStateMachineGraph.h"
#include "AnimationStateMachineSchema.h"
#include "AnimGraphNode_StateMachineBase.h"
#include "AnimStateEntryNode.h"
#include "AnimStateNode.h"
#include "AnimStateNodeBase.h"
#include "AnimStateTransitionNode.h"
#include "EdGraph/EdGraph.h"
#include "Engine/Blueprint.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Misc/PackageName.h"
#include "ScopedTransaction.h"
#include "UObject/SavePackage.h"

namespace AnimBlueprintToolsetPrivate
{
	void RaiseToolError(const FString& Message)
	{
		UKismetSystemLibrary::RaiseScriptError(FString::Printf(TEXT("AnimBlueprintToolset: %s"), *Message));
	}

	FString NodeId(const UEdGraphNode* Node)
	{
		return Node && Node->NodeGuid.IsValid()
			? Node->NodeGuid.ToString(EGuidFormats::DigitsWithHyphens)
			: FString();
	}

	FString GetStateMachineName(const UAnimationStateMachineGraph* StateMachineGraph)
	{
		if (!StateMachineGraph)
		{
			return FString();
		}

		if (StateMachineGraph->OwnerAnimGraphNode)
		{
			return StateMachineGraph->OwnerAnimGraphNode->GetStateMachineName();
		}

		return StateMachineGraph->GetName();
	}

	TArray<UAnimationStateMachineGraph*> GetStateMachineGraphs(const UAnimBlueprint* AnimBlueprint)
	{
		TArray<UAnimationStateMachineGraph*> Result;
		if (!AnimBlueprint)
		{
			return Result;
		}

		TArray<UEdGraph*> AllGraphs;
		AnimBlueprint->GetAllGraphs(AllGraphs);

		TSet<UAnimationStateMachineGraph*> SeenGraphs;
		for (UEdGraph* Graph : AllGraphs)
		{
			if (UAnimationStateMachineGraph* StateMachineGraph = Cast<UAnimationStateMachineGraph>(Graph))
			{
				if (!SeenGraphs.Contains(StateMachineGraph))
				{
					SeenGraphs.Add(StateMachineGraph);
					Result.Add(StateMachineGraph);
				}
			}
		}

		Result.Sort([](const UAnimationStateMachineGraph& Left, const UAnimationStateMachineGraph& Right)
		{
			return GetStateMachineName(&Left) < GetStateMachineName(&Right);
		});
		return Result;
	}

	UAnimationStateMachineGraph* FindStateMachineGraph(const UAnimBlueprint* AnimBlueprint, const FString& StateMachineName)
	{
		if (!AnimBlueprint || StateMachineName.IsEmpty())
		{
			return nullptr;
		}

		for (UAnimationStateMachineGraph* StateMachineGraph : GetStateMachineGraphs(AnimBlueprint))
		{
			if (GetStateMachineName(StateMachineGraph).Equals(StateMachineName, ESearchCase::IgnoreCase)
				|| StateMachineGraph->GetName().Equals(StateMachineName, ESearchCase::IgnoreCase))
			{
				return StateMachineGraph;
			}
		}

		return nullptr;
	}

	UAnimStateNode* FindState(UAnimationStateMachineGraph* StateMachineGraph, const FString& StateName)
	{
		if (!StateMachineGraph || StateName.IsEmpty())
		{
			return nullptr;
		}

		for (UEdGraphNode* Node : StateMachineGraph->Nodes)
		{
			UAnimStateNode* StateNode = Cast<UAnimStateNode>(Node);
			if (StateNode && StateNode->GetStateName().Equals(StateName, ESearchCase::IgnoreCase))
			{
				return StateNode;
			}
		}

		return nullptr;
	}

	const UAnimStateNode* FindState(const UAnimationStateMachineGraph* StateMachineGraph, const FString& StateName)
	{
		return FindState(const_cast<UAnimationStateMachineGraph*>(StateMachineGraph), StateName);
	}

	UAnimStateTransitionNode* FindTransition(
		UAnimationStateMachineGraph* StateMachineGraph,
		const FString& PreviousState,
		const FString& NextState)
	{
		if (!StateMachineGraph || PreviousState.IsEmpty() || NextState.IsEmpty())
		{
			return nullptr;
		}

		for (UEdGraphNode* Node : StateMachineGraph->Nodes)
		{
			UAnimStateTransitionNode* TransitionNode = Cast<UAnimStateTransitionNode>(Node);
			if (!TransitionNode)
			{
				continue;
			}

			const UAnimStateNodeBase* PreviousStateNode = TransitionNode->GetPreviousState();
			const UAnimStateNodeBase* NextStateNode = TransitionNode->GetNextState();
			if (PreviousStateNode
				&& NextStateNode
				&& PreviousStateNode->GetStateName().Equals(PreviousState, ESearchCase::IgnoreCase)
				&& NextStateNode->GetStateName().Equals(NextState, ESearchCase::IgnoreCase))
			{
				return TransitionNode;
			}
		}

		return nullptr;
	}

	const UAnimStateTransitionNode* FindTransition(
		const UAnimationStateMachineGraph* StateMachineGraph,
		const FString& PreviousState,
		const FString& NextState)
	{
		return FindTransition(const_cast<UAnimationStateMachineGraph*>(StateMachineGraph), PreviousState, NextState);
	}

	FAnimBlueprintToolsetStateInfo MakeStateInfo(const UAnimStateNode* StateNode)
	{
		FAnimBlueprintToolsetStateInfo Result;
		if (!StateNode)
		{
			return Result;
		}

		Result.Name = StateNode->GetStateName();
		Result.NodeId = NodeId(StateNode);
		Result.BoundGraphPath = StateNode->BoundGraph ? StateNode->BoundGraph->GetPathName() : FString();
		Result.StateType = StaticEnum<EAnimStateType>()->GetNameStringByValue(StateNode->StateType.GetValue());
		Result.NodePosX = StateNode->NodePosX;
		Result.NodePosY = StateNode->NodePosY;
		Result.bAlwaysResetOnEntry = StateNode->bAlwaysResetOnEntry;
		return Result;
	}

	FAnimBlueprintToolsetTransitionSettings MakeTransitionSettings(const UAnimStateTransitionNode* TransitionNode)
	{
		FAnimBlueprintToolsetTransitionSettings Result;
		if (!TransitionNode)
		{
			return Result;
		}

		Result.PriorityOrder = TransitionNode->PriorityOrder;
		Result.CrossfadeDuration = TransitionNode->CrossfadeDuration;
		Result.BlendMode = TransitionNode->BlendMode;
		Result.bAutomaticRuleBasedOnSequencePlayerInState = TransitionNode->bAutomaticRuleBasedOnSequencePlayerInState;
		Result.AutomaticRuleTriggerTime = TransitionNode->AutomaticRuleTriggerTime;
		Result.MinTimeBeforeReentry = TransitionNode->MinTimeBeforeReentry;
		Result.bBidirectional = TransitionNode->Bidirectional;
		Result.bDisabled = TransitionNode->bDisabled;
		return Result;
	}

	FAnimBlueprintToolsetTransitionInfo MakeTransitionInfo(const UAnimStateTransitionNode* TransitionNode)
	{
		FAnimBlueprintToolsetTransitionInfo Result;
		if (!TransitionNode)
		{
			return Result;
		}

		const UAnimStateNodeBase* PreviousStateNode = TransitionNode->GetPreviousState();
		const UAnimStateNodeBase* NextStateNode = TransitionNode->GetNextState();
		Result.NodeId = NodeId(TransitionNode);
		Result.PreviousState = PreviousStateNode ? PreviousStateNode->GetStateName() : FString();
		Result.NextState = NextStateNode ? NextStateNode->GetStateName() : FString();
		Result.BoundGraphPath = TransitionNode->BoundGraph ? TransitionNode->BoundGraph->GetPathName() : FString();
		Result.CustomTransitionGraphPath = TransitionNode->CustomTransitionGraph
			? TransitionNode->CustomTransitionGraph->GetPathName()
			: FString();
		Result.Settings = MakeTransitionSettings(TransitionNode);
		return Result;
	}

	FAnimBlueprintToolsetStateMachineSummary MakeStateMachineSummary(const UAnimationStateMachineGraph* StateMachineGraph)
	{
		FAnimBlueprintToolsetStateMachineSummary Result;
		if (!StateMachineGraph)
		{
			return Result;
		}

		Result.Name = GetStateMachineName(StateMachineGraph);
		Result.GraphPath = StateMachineGraph->GetPathName();
		Result.OwnerNodePath = StateMachineGraph->OwnerAnimGraphNode
			? StateMachineGraph->OwnerAnimGraphNode->GetPathName()
			: FString();

		for (const UEdGraphNode* Node : StateMachineGraph->Nodes)
		{
			Result.StateCount += Node && Node->IsA<UAnimStateNode>() ? 1 : 0;
			Result.TransitionCount += Node && Node->IsA<UAnimStateTransitionNode>() ? 1 : 0;
		}

		return Result;
	}

	FAnimBlueprintToolsetStateMachineInfo MakeStateMachineInfo(
		const UAnimBlueprint* AnimBlueprint,
		const UAnimationStateMachineGraph* StateMachineGraph)
	{
		FAnimBlueprintToolsetStateMachineInfo Result;
		if (!AnimBlueprint || !StateMachineGraph)
		{
			return Result;
		}

		Result.AnimBlueprintPath = AnimBlueprint->GetPathName();
		Result.Name = GetStateMachineName(StateMachineGraph);
		Result.GraphPath = StateMachineGraph->GetPathName();
		Result.OwnerNodePath = StateMachineGraph->OwnerAnimGraphNode
			? StateMachineGraph->OwnerAnimGraphNode->GetPathName()
			: FString();

		if (StateMachineGraph->EntryNode)
		{
			if (const UAnimStateNodeBase* EntryState = Cast<UAnimStateNodeBase>(StateMachineGraph->EntryNode->GetOutputNode()))
			{
				Result.EntryState = EntryState->GetStateName();
			}
		}

		for (const UEdGraphNode* Node : StateMachineGraph->Nodes)
		{
			if (const UAnimStateNode* StateNode = Cast<UAnimStateNode>(Node))
			{
				Result.States.Add(MakeStateInfo(StateNode));
			}
			else if (const UAnimStateTransitionNode* TransitionNode = Cast<UAnimStateTransitionNode>(Node))
			{
				Result.Transitions.Add(MakeTransitionInfo(TransitionNode));
			}
		}

		Result.States.Sort([](const FAnimBlueprintToolsetStateInfo& Left, const FAnimBlueprintToolsetStateInfo& Right)
		{
			return Left.Name < Right.Name;
		});
		Result.Transitions.Sort([](
			const FAnimBlueprintToolsetTransitionInfo& Left,
			const FAnimBlueprintToolsetTransitionInfo& Right)
		{
			if (Left.PreviousState == Right.PreviousState)
			{
				return Left.NextState < Right.NextState;
			}
			return Left.PreviousState < Right.PreviousState;
		});

		return Result;
	}

	bool ValidateTransitionSettings(const FAnimBlueprintToolsetTransitionSettings& Settings)
	{
		if (Settings.PriorityOrder < 0)
		{
			RaiseToolError(TEXT("PriorityOrder must be zero or greater."));
			return false;
		}

		if (Settings.CrossfadeDuration < 0.0f)
		{
			RaiseToolError(TEXT("CrossfadeDuration must be zero or greater."));
			return false;
		}

		if (Settings.MinTimeBeforeReentry < -1.0f)
		{
			RaiseToolError(TEXT("MinTimeBeforeReentry must be -1 or greater."));
			return false;
		}

		return true;
	}

	void ApplyTransitionSettings(
		UAnimStateTransitionNode* TransitionNode,
		const FAnimBlueprintToolsetTransitionSettings& Settings)
	{
		TransitionNode->Modify();
		TransitionNode->PriorityOrder = Settings.PriorityOrder;
		TransitionNode->CrossfadeDuration = Settings.CrossfadeDuration;
		TransitionNode->BlendMode = Settings.BlendMode;
		TransitionNode->bAutomaticRuleBasedOnSequencePlayerInState =
			Settings.bAutomaticRuleBasedOnSequencePlayerInState;
		TransitionNode->AutomaticRuleTriggerTime = Settings.AutomaticRuleTriggerTime;
		TransitionNode->MinTimeBeforeReentry = Settings.MinTimeBeforeReentry;
		TransitionNode->Bidirectional = Settings.bBidirectional;
		TransitionNode->bDisabled = Settings.bDisabled;
	}

	bool SaveAnimBlueprint(UAnimBlueprint* AnimBlueprint)
	{
		UPackage* Package = AnimBlueprint ? AnimBlueprint->GetOutermost() : nullptr;
		if (!Package)
		{
			RaiseToolError(TEXT("The Animation Blueprint has no package to save."));
			return false;
		}

		const FString PackageFilename = FPackageName::LongPackageNameToFilename(
			Package->GetName(),
			FPackageName::GetAssetPackageExtension());
		if (PackageFilename.IsEmpty())
		{
			RaiseToolError(FString::Printf(TEXT("Could not resolve a filename for package '%s'."), *Package->GetName()));
			return false;
		}

		FSavePackageArgs SaveArgs;
		SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
		SaveArgs.SaveFlags = SAVE_NoError;
		if (!UPackage::SavePackage(Package, AnimBlueprint, *PackageFilename, SaveArgs))
		{
			RaiseToolError(FString::Printf(TEXT("Failed to save package '%s'."), *Package->GetName()));
			return false;
		}

		return true;
	}

	bool FinalizeChange(
		UAnimBlueprint* AnimBlueprint,
		const bool bStructuralChange,
		const bool bCompileBlueprint,
		const bool bSaveAsset)
	{
		if (bStructuralChange)
		{
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(AnimBlueprint);
		}
		else
		{
			FBlueprintEditorUtils::MarkBlueprintAsModified(AnimBlueprint);
		}

		AnimBlueprint->GetOutermost()->MarkPackageDirty();

		if (bCompileBlueprint)
		{
			FKismetEditorUtilities::CompileBlueprint(AnimBlueprint);
		}

		return !bSaveAsset || SaveAnimBlueprint(AnimBlueprint);
	}

	UAnimationStateMachineGraph* RequireStateMachine(
		const UAnimBlueprint* AnimBlueprint,
		const FString& StateMachineName)
	{
		if (!AnimBlueprint)
		{
			RaiseToolError(TEXT("AnimBlueprint is required."));
			return nullptr;
		}

		if (StateMachineName.TrimStartAndEnd().IsEmpty())
		{
			RaiseToolError(TEXT("StateMachineName is required."));
			return nullptr;
		}

		UAnimationStateMachineGraph* StateMachineGraph = FindStateMachineGraph(AnimBlueprint, StateMachineName);
		if (!StateMachineGraph)
		{
			RaiseToolError(FString::Printf(
				TEXT("State machine '%s' was not found in '%s'."),
				*StateMachineName,
				*AnimBlueprint->GetPathName()));
		}
		return StateMachineGraph;
	}
}

TArray<FAnimBlueprintToolsetStateMachineSummary> UAnimBlueprintToolset::ListStateMachines(
	const UAnimBlueprint* AnimBlueprint)
{
	using namespace AnimBlueprintToolsetPrivate;

	if (!AnimBlueprint)
	{
		RaiseToolError(TEXT("AnimBlueprint is required."));
		return {};
	}

	TArray<FAnimBlueprintToolsetStateMachineSummary> Result;
	for (const UAnimationStateMachineGraph* StateMachineGraph : GetStateMachineGraphs(AnimBlueprint))
	{
		Result.Add(MakeStateMachineSummary(StateMachineGraph));
	}
	return Result;
}

FAnimBlueprintToolsetStateMachineInfo UAnimBlueprintToolset::GetStateMachine(
	const UAnimBlueprint* AnimBlueprint,
	const FString& StateMachineName)
{
	using namespace AnimBlueprintToolsetPrivate;

	const UAnimationStateMachineGraph* StateMachineGraph = RequireStateMachine(AnimBlueprint, StateMachineName);
	return StateMachineGraph ? MakeStateMachineInfo(AnimBlueprint, StateMachineGraph) : FAnimBlueprintToolsetStateMachineInfo();
}

FAnimBlueprintToolsetStateInfo UAnimBlueprintToolset::CreateState(
	UAnimBlueprint* AnimBlueprint,
	const FString& StateMachineName,
	const FString& StateName,
	const int32 NodePosX,
	const int32 NodePosY,
	const bool bAlwaysResetOnEntry,
	const bool bCompileBlueprint,
	const bool bSaveAsset)
{
	using namespace AnimBlueprintToolsetPrivate;

	UAnimationStateMachineGraph* StateMachineGraph = RequireStateMachine(AnimBlueprint, StateMachineName);
	const FString TrimmedStateName = StateName.TrimStartAndEnd();
	if (!StateMachineGraph)
	{
		return {};
	}
	if (TrimmedStateName.IsEmpty())
	{
		RaiseToolError(TEXT("StateName is required."));
		return {};
	}
	if (FindState(StateMachineGraph, TrimmedStateName))
	{
		RaiseToolError(FString::Printf(
			TEXT("State '%s' already exists in state machine '%s'."),
			*TrimmedStateName,
			*GetStateMachineName(StateMachineGraph)));
		return {};
	}

	const FScopedTransaction Transaction(NSLOCTEXT(
		"AnimBlueprintToolset",
		"CreateState",
		"Create Animation Blueprint State"));
	AnimBlueprint->Modify();
	StateMachineGraph->Modify();

	UAnimStateNode* StateNode = FEdGraphSchemaAction_NewStateNode::SpawnNodeFromTemplate<UAnimStateNode>(
		StateMachineGraph,
		NewObject<UAnimStateNode>(),
		FVector2f(static_cast<float>(NodePosX), static_cast<float>(NodePosY)),
		false);
	if (!StateNode)
	{
		RaiseToolError(FString::Printf(TEXT("Failed to create state '%s'."), *TrimmedStateName));
		return {};
	}

	StateNode->Modify();
	if (StateNode->BoundGraph)
	{
		FBlueprintEditorUtils::RenameGraph(StateNode->BoundGraph, TrimmedStateName);
	}
	StateNode->bAlwaysResetOnEntry = bAlwaysResetOnEntry;

	if (!FinalizeChange(AnimBlueprint, true, bCompileBlueprint, bSaveAsset))
	{
		return {};
	}
	return MakeStateInfo(StateNode);
}

bool UAnimBlueprintToolset::DeleteState(
	UAnimBlueprint* AnimBlueprint,
	const FString& StateMachineName,
	const FString& StateName,
	const bool bCompileBlueprint,
	const bool bSaveAsset)
{
	using namespace AnimBlueprintToolsetPrivate;

	UAnimationStateMachineGraph* StateMachineGraph = RequireStateMachine(AnimBlueprint, StateMachineName);
	if (!StateMachineGraph)
	{
		return false;
	}

	UAnimStateNode* StateNode = FindState(StateMachineGraph, StateName);
	if (!StateNode)
	{
		RaiseToolError(FString::Printf(
			TEXT("State '%s' was not found in state machine '%s'."),
			*StateName,
			*GetStateMachineName(StateMachineGraph)));
		return false;
	}

	const FScopedTransaction Transaction(NSLOCTEXT(
		"AnimBlueprintToolset",
		"DeleteState",
		"Delete Animation Blueprint State"));
	AnimBlueprint->Modify();
	StateMachineGraph->Modify();

	TArray<UAnimStateTransitionNode*> ConnectedTransitions;
	StateNode->GetTransitionList(ConnectedTransitions, false);
	for (UAnimStateTransitionNode* TransitionNode : ConnectedTransitions)
	{
		if (TransitionNode)
		{
			TransitionNode->Modify();
			TransitionNode->DestroyNode();
		}
	}

	StateNode->Modify();
	StateNode->DestroyNode();
	return FinalizeChange(AnimBlueprint, true, bCompileBlueprint, bSaveAsset);
}

FAnimBlueprintToolsetTransitionInfo UAnimBlueprintToolset::CreateTransition(
	UAnimBlueprint* AnimBlueprint,
	const FString& StateMachineName,
	const FString& PreviousState,
	const FString& NextState,
	const FAnimBlueprintToolsetTransitionSettings& Settings,
	const bool bCompileBlueprint,
	const bool bSaveAsset)
{
	using namespace AnimBlueprintToolsetPrivate;

	UAnimationStateMachineGraph* StateMachineGraph = RequireStateMachine(AnimBlueprint, StateMachineName);
	if (!StateMachineGraph || !ValidateTransitionSettings(Settings))
	{
		return {};
	}

	UAnimStateNode* PreviousStateNode = FindState(StateMachineGraph, PreviousState);
	UAnimStateNode* NextStateNode = FindState(StateMachineGraph, NextState);
	if (!PreviousStateNode || !NextStateNode)
	{
		RaiseToolError(FString::Printf(
			TEXT("Transition endpoints must both be normal states in '%s': '%s' -> '%s'."),
			*GetStateMachineName(StateMachineGraph),
			*PreviousState,
			*NextState));
		return {};
	}
	if (FindTransition(StateMachineGraph, PreviousState, NextState))
	{
		RaiseToolError(FString::Printf(
			TEXT("Transition '%s' -> '%s' already exists in state machine '%s'."),
			*PreviousState,
			*NextState,
			*GetStateMachineName(StateMachineGraph)));
		return {};
	}

	const FScopedTransaction Transaction(NSLOCTEXT(
		"AnimBlueprintToolset",
		"CreateTransition",
		"Create Animation Blueprint Transition"));
	AnimBlueprint->Modify();
	StateMachineGraph->Modify();

	UAnimStateTransitionNode* TransitionNode = NewObject<UAnimStateTransitionNode>(
		StateMachineGraph,
		UAnimStateTransitionNode::StaticClass(),
		NAME_None,
		RF_Transactional);
	TransitionNode->CreateNewGuid();
	TransitionNode->NodePosX = (PreviousStateNode->NodePosX + NextStateNode->NodePosX) / 2;
	TransitionNode->NodePosY = (PreviousStateNode->NodePosY + NextStateNode->NodePosY) / 2;
	TransitionNode->AllocateDefaultPins();
	StateMachineGraph->AddNode(TransitionNode, true, false);
	TransitionNode->PostPlacedNewNode();
	TransitionNode->CreateConnections(PreviousStateNode, NextStateNode);
	ApplyTransitionSettings(TransitionNode, Settings);

	if (!FinalizeChange(AnimBlueprint, true, bCompileBlueprint, bSaveAsset))
	{
		return {};
	}
	return MakeTransitionInfo(TransitionNode);
}

bool UAnimBlueprintToolset::DeleteTransition(
	UAnimBlueprint* AnimBlueprint,
	const FString& StateMachineName,
	const FString& PreviousState,
	const FString& NextState,
	const bool bCompileBlueprint,
	const bool bSaveAsset)
{
	using namespace AnimBlueprintToolsetPrivate;

	UAnimationStateMachineGraph* StateMachineGraph = RequireStateMachine(AnimBlueprint, StateMachineName);
	if (!StateMachineGraph)
	{
		return false;
	}

	UAnimStateTransitionNode* TransitionNode = FindTransition(StateMachineGraph, PreviousState, NextState);
	if (!TransitionNode)
	{
		RaiseToolError(FString::Printf(
			TEXT("Transition '%s' -> '%s' was not found in state machine '%s'."),
			*PreviousState,
			*NextState,
			*GetStateMachineName(StateMachineGraph)));
		return false;
	}

	const FScopedTransaction Transaction(NSLOCTEXT(
		"AnimBlueprintToolset",
		"DeleteTransition",
		"Delete Animation Blueprint Transition"));
	AnimBlueprint->Modify();
	StateMachineGraph->Modify();
	TransitionNode->Modify();
	TransitionNode->DestroyNode();
	return FinalizeChange(AnimBlueprint, true, bCompileBlueprint, bSaveAsset);
}

FAnimBlueprintToolsetTransitionInfo UAnimBlueprintToolset::SetTransitionSettings(
	UAnimBlueprint* AnimBlueprint,
	const FString& StateMachineName,
	const FString& PreviousState,
	const FString& NextState,
	const FAnimBlueprintToolsetTransitionSettings& Settings,
	const bool bCompileBlueprint,
	const bool bSaveAsset)
{
	using namespace AnimBlueprintToolsetPrivate;

	UAnimationStateMachineGraph* StateMachineGraph = RequireStateMachine(AnimBlueprint, StateMachineName);
	if (!StateMachineGraph || !ValidateTransitionSettings(Settings))
	{
		return {};
	}

	UAnimStateTransitionNode* TransitionNode = FindTransition(StateMachineGraph, PreviousState, NextState);
	if (!TransitionNode)
	{
		RaiseToolError(FString::Printf(
			TEXT("Transition '%s' -> '%s' was not found in state machine '%s'."),
			*PreviousState,
			*NextState,
			*GetStateMachineName(StateMachineGraph)));
		return {};
	}

	const FScopedTransaction Transaction(NSLOCTEXT(
		"AnimBlueprintToolset",
		"SetTransitionSettings",
		"Set Animation Blueprint Transition Settings"));
	AnimBlueprint->Modify();
	ApplyTransitionSettings(TransitionNode, Settings);

	if (!FinalizeChange(AnimBlueprint, false, bCompileBlueprint, bSaveAsset))
	{
		return {};
	}
	return MakeTransitionInfo(TransitionNode);
}
