#include "PlaytestToolset.h"

#include "Containers/Ticker.h"
#include "Editor.h"
#include "Engine/GameInstance.h"
#include "Engine/LocalPlayer.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "Kismet/KismetSystemLibrary.h"
#include "ToolsetRegistry/ToolCallAsyncResultVoid.h"
#include "UObject/StrongObjectPtr.h"

namespace UE::UnrealMCPToolsets::Private
{
	UEnhancedInputLocalPlayerSubsystem* ResolveInputSubsystem(const int32 PlayerIndex)
	{
		if (PlayerIndex < 0)
		{
			UKismetSystemLibrary::RaiseScriptError(TEXT("PlayerIndex must be zero or greater."));
			return nullptr;
		}

		if (!GEditor || !GEditor->PlayWorld)
		{
			UKismetSystemLibrary::RaiseScriptError(TEXT("An active in-process PIE session is required."));
			return nullptr;
		}

		UGameInstance* GameInstance = GEditor->PlayWorld->GetGameInstance();
		ULocalPlayer* LocalPlayer = GameInstance ? GameInstance->GetLocalPlayerByIndex(PlayerIndex) : nullptr;
		if (!LocalPlayer)
		{
			UKismetSystemLibrary::RaiseScriptError(FString::Printf(
				TEXT("No local player exists at index %d."), PlayerIndex));
			return nullptr;
		}

		UEnhancedInputLocalPlayerSubsystem* Subsystem =
			LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>();
		if (!Subsystem)
		{
			UKismetSystemLibrary::RaiseScriptError(FString::Printf(
				TEXT("Enhanced Input is unavailable for local player %d."), PlayerIndex));
		}
		return Subsystem;
	}

	bool ValidateInputAction(const UInputAction* InputAction)
	{
		if (InputAction)
		{
			return true;
		}

		UKismetSystemLibrary::RaiseScriptError(TEXT("InputAction cannot be null."));
		return false;
	}

	FInputActionValue MakeInputValue(const UInputAction& InputAction, const FVector& Value)
	{
		switch (InputAction.ValueType)
		{
		case EInputActionValueType::Boolean:
			return FInputActionValue(!FMath::IsNearlyZero(Value.X));
		case EInputActionValueType::Axis1D:
			return FInputActionValue(static_cast<float>(Value.X));
		case EInputActionValueType::Axis2D:
			return FInputActionValue(FVector2D(Value.X, Value.Y));
		case EInputActionValueType::Axis3D:
		default:
			return FInputActionValue(Value);
		}
	}
}

bool UPlaytestToolset::InjectInputAction(
	const UInputAction* InputAction,
	const FVector Value,
	const int32 PlayerIndex)
{
	using namespace UE::UnrealMCPToolsets::Private;
	UEnhancedInputLocalPlayerSubsystem* Subsystem = ResolveInputSubsystem(PlayerIndex);
	if (!Subsystem || !ValidateInputAction(InputAction))
	{
		return false;
	}

	Subsystem->InjectInputForAction(InputAction, MakeInputValue(*InputAction, Value), {}, {});
	return true;
}

bool UPlaytestToolset::StartInputAction(
	const UInputAction* InputAction,
	const FVector Value,
	const int32 PlayerIndex)
{
	using namespace UE::UnrealMCPToolsets::Private;
	UEnhancedInputLocalPlayerSubsystem* Subsystem = ResolveInputSubsystem(PlayerIndex);
	if (!Subsystem || !ValidateInputAction(InputAction))
	{
		return false;
	}

	Subsystem->StartContinuousInputInjectionForAction(
		InputAction,
		MakeInputValue(*InputAction, Value),
		{},
		{});
	return true;
}

bool UPlaytestToolset::UpdateInputAction(
	const UInputAction* InputAction,
	const FVector Value,
	const int32 PlayerIndex)
{
	using namespace UE::UnrealMCPToolsets::Private;
	UEnhancedInputLocalPlayerSubsystem* Subsystem = ResolveInputSubsystem(PlayerIndex);
	if (!Subsystem || !ValidateInputAction(InputAction))
	{
		return false;
	}

	if (!Subsystem->HasContinuousInputInjectionForAction(InputAction))
	{
		UKismetSystemLibrary::RaiseScriptError(TEXT("The input action is not being injected continuously."));
		return false;
	}

	Subsystem->UpdateValueOfContinuousInputInjectionForAction(
		InputAction,
		MakeInputValue(*InputAction, Value));
	return true;
}

bool UPlaytestToolset::StopInputAction(const UInputAction* InputAction, const int32 PlayerIndex)
{
	using namespace UE::UnrealMCPToolsets::Private;
	UEnhancedInputLocalPlayerSubsystem* Subsystem = ResolveInputSubsystem(PlayerIndex);
	if (!Subsystem || !ValidateInputAction(InputAction))
	{
		return false;
	}

	const bool bWasInjected = Subsystem->HasContinuousInputInjectionForAction(InputAction);
	Subsystem->StopContinuousInputInjectionForAction(InputAction);
	return bWasInjected;
}

bool UPlaytestToolset::IsInputActionInjected(const UInputAction* InputAction, const int32 PlayerIndex)
{
	using namespace UE::UnrealMCPToolsets::Private;
	UEnhancedInputLocalPlayerSubsystem* Subsystem = ResolveInputSubsystem(PlayerIndex);
	return Subsystem && ValidateInputAction(InputAction)
		&& Subsystem->HasContinuousInputInjectionForAction(InputAction);
}

UToolCallAsyncResultVoid* UPlaytestToolset::InjectInputActionForDuration(
	const UInputAction* InputAction,
	const FVector Value,
	const float DurationSeconds,
	const int32 PlayerIndex)
{
	using namespace UE::UnrealMCPToolsets::Private;
	UToolCallAsyncResultVoid* Result = NewObject<UToolCallAsyncResultVoid>();

	if (!ValidateInputAction(InputAction))
	{
		Result->SetError(TEXT("InputAction cannot be null."));
		return Result;
	}
	if (DurationSeconds <= 0.0f || DurationSeconds > 30.0f)
	{
		Result->SetError(TEXT("DurationSeconds must be greater than zero and no more than 30 seconds."));
		return Result;
	}

	UEnhancedInputLocalPlayerSubsystem* Subsystem = ResolveInputSubsystem(PlayerIndex);
	if (!Subsystem)
	{
		Result->SetError(TEXT("Enhanced Input is unavailable for the requested PIE player."));
		return Result;
	}
	if (Subsystem->HasContinuousInputInjectionForAction(InputAction))
	{
		Result->SetError(TEXT("The input action is already being injected continuously."));
		return Result;
	}

	Subsystem->StartContinuousInputInjectionForAction(
		InputAction,
		MakeInputValue(*InputAction, Value),
		{},
		{});

	TStrongObjectPtr<UToolCallAsyncResultVoid> StrongResult(Result);
	TStrongObjectPtr<UInputAction> StrongAction(const_cast<UInputAction*>(InputAction));
	TWeakObjectPtr<UEnhancedInputLocalPlayerSubsystem> WeakSubsystem(Subsystem);
	const double EndTime = FPlatformTime::Seconds() + DurationSeconds;

	FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda(
		[StrongResult, StrongAction, WeakSubsystem, EndTime](float) mutable -> bool
		{
			UEnhancedInputLocalPlayerSubsystem* CurrentSubsystem = WeakSubsystem.Get();
			if (!CurrentSubsystem)
			{
				StrongResult->SetError(TEXT("PIE ended before input injection completed."));
				StrongResult.Reset();
				StrongAction.Reset();
				return false;
			}

			if (FPlatformTime::Seconds() < EndTime)
			{
				return true;
			}

			CurrentSubsystem->StopContinuousInputInjectionForAction(StrongAction.Get());
			StrongResult->SetCompleted();
			StrongResult.Reset();
			StrongAction.Reset();
			return false;
		}));

	return Result;
}
