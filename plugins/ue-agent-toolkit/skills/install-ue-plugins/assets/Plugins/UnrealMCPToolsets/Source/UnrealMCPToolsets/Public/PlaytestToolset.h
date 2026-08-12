#pragma once

#include "CoreMinimal.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "PlaytestToolset.generated.h"

class UInputAction;
class UToolCallAsyncResultVoid;

/**
 * MCP tools that fill the runtime-input gap between the engine's PIE,
 * scene, actor, object, Slate, log, capture, and Automation toolsets.
 */
UCLASS(BlueprintType)
class UNREALMCPTOOLSETS_API UPlaytestToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	virtual FString GetToolsetVersion() const override
	{
		return TEXT("0.1.0");
	}

	/** Injects an Enhanced Input action for the current frame of an active PIE session. */
	UFUNCTION(meta = (AICallable), Category = "Playtest|Input")
	static bool InjectInputAction(
		const UInputAction* InputAction,
		FVector Value = FVector::ZeroVector,
		int32 PlayerIndex = 0);

	/** Starts injecting an Enhanced Input action every frame until it is stopped. */
	UFUNCTION(meta = (AICallable), Category = "Playtest|Input")
	static bool StartInputAction(
		const UInputAction* InputAction,
		FVector Value = FVector::ZeroVector,
		int32 PlayerIndex = 0);

	/** Updates the value of an active continuous Enhanced Input injection. */
	UFUNCTION(meta = (AICallable), Category = "Playtest|Input")
	static bool UpdateInputAction(
		const UInputAction* InputAction,
		FVector Value = FVector::ZeroVector,
		int32 PlayerIndex = 0);

	/** Stops a continuous Enhanced Input injection. Returns whether it was active. */
	UFUNCTION(meta = (AICallable), Category = "Playtest|Input")
	static bool StopInputAction(const UInputAction* InputAction, int32 PlayerIndex = 0);

	/** Returns whether the action is currently being injected continuously. */
	UFUNCTION(meta = (AICallable), Category = "Playtest|Input")
	static bool IsInputActionInjected(const UInputAction* InputAction, int32 PlayerIndex = 0);

	/**
	 * Injects an Enhanced Input action every frame for a bounded duration, then
	 * stops it and completes the MCP call. Duration must be greater than zero
	 * and no more than 30 seconds. An action already being injected continuously
	 * is rejected so this call cannot take ownership of another input sequence.
	 */
	UFUNCTION(meta = (AICallable), Category = "Playtest|Input")
	static UToolCallAsyncResultVoid* InjectInputActionForDuration(
		const UInputAction* InputAction,
		FVector Value = FVector::ZeroVector,
		float DurationSeconds = 0.1f,
		int32 PlayerIndex = 0);
};
