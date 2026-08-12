#include "Animation/AnimBlueprintToolset.h"
#include "Modules/ModuleManager.h"
#include "PlaytestToolset.h"
#include "ToolsetRegistry/UToolsetRegistry.h"

class FUnrealMCPToolsetsModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		UToolsetRegistry::RegisterToolsetClass(UAnimBlueprintToolset::StaticClass());
		UToolsetRegistry::RegisterToolsetClass(UPlaytestToolset::StaticClass());
	}

	virtual void ShutdownModule() override
	{
		UToolsetRegistry::UnregisterToolsetClass(UPlaytestToolset::StaticClass());
		UToolsetRegistry::UnregisterToolsetClass(UAnimBlueprintToolset::StaticClass());
	}
};

IMPLEMENT_MODULE(FUnrealMCPToolsetsModule, UnrealMCPToolsets)
