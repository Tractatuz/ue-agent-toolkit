using UnrealBuildTool;

public class UnrealMCPToolsets : ModuleRules
{
	public UnrealMCPToolsets(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"ToolsetRegistry"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"AnimGraph",
			"EnhancedInput",
			"Kismet",
			"UnrealEd"
		});
	}
}
