// Copyright Epic Games, Inc. All Rights Reserved.

#include "TexNamingImporter.h"
#include "TexNamingImporterStyle.h"
#include "TexNamingImporterCommands.h"
#include "LevelEditor.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "ToolMenus.h"

static const FName TexNamingImporterTabName("TexNamingImporter");

#define LOCTEXT_NAMESPACE "FTexNamingImporterModule"

void FTexNamingImporterModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	
	FTexNamingImporterStyle::Initialize();
	FTexNamingImporterStyle::ReloadTextures();

	FTexNamingImporterCommands::Register();
	
	PluginCommands = MakeShareable(new FUICommandList);

	PluginCommands->MapAction(
		FTexNamingImporterCommands::Get().OpenPluginWindow,
		FExecuteAction::CreateRaw(this, &FTexNamingImporterModule::PluginButtonClicked),
		FCanExecuteAction());

	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FTexNamingImporterModule::RegisterMenus));
	
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(TexNamingImporterTabName, FOnSpawnTab::CreateRaw(this, &FTexNamingImporterModule::OnSpawnPluginTab))
		.SetDisplayName(LOCTEXT("FTexNamingImporterTabTitle", "TexNamingImporter"))
		.SetMenuType(ETabSpawnerMenuType::Hidden);
}

void FTexNamingImporterModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

	UToolMenus::UnRegisterStartupCallback(this);

	UToolMenus::UnregisterOwner(this);

	FTexNamingImporterStyle::Shutdown();

	FTexNamingImporterCommands::Unregister();

	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(TexNamingImporterTabName);
}

TSharedRef<SDockTab> FTexNamingImporterModule::OnSpawnPluginTab(const FSpawnTabArgs& SpawnTabArgs)
{
	FText WidgetText = FText::Format(
		LOCTEXT("WindowWidgetText", "Add code to {0} in {1} to override this window's contents"),
		FText::FromString(TEXT("FTexNamingImporterModule::OnSpawnPluginTab")),
		FText::FromString(TEXT("TexNamingImporter.cpp"))
		);

	return SNew(SDockTab)
		.TabRole(ETabRole::NomadTab)
		[
			// Put your tab content here!
			SNew(SBox)
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Center)
			[
				SNew(STextBlock)
				.Text(WidgetText)
			]
		];
}

void FTexNamingImporterModule::PluginButtonClicked()
{
	FGlobalTabmanager::Get()->TryInvokeTab(TexNamingImporterTabName);
}

void FTexNamingImporterModule::RegisterMenus()
{
	// Owner will be used for cleanup in call to UToolMenus::UnregisterOwner
	FToolMenuOwnerScoped OwnerScoped(this);

	{
		UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
		{
			FToolMenuSection& Section = Menu->FindOrAddSection("WindowLayout");
			Section.AddMenuEntryWithCommandList(FTexNamingImporterCommands::Get().OpenPluginWindow, PluginCommands);
		}
	}

	{
		UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar");
		{
			FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("Settings");
			{
				FToolMenuEntry& Entry = Section.AddEntry(FToolMenuEntry::InitToolBarButton(FTexNamingImporterCommands::Get().OpenPluginWindow));
				Entry.SetCommandList(PluginCommands);
			}
		}
	}
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FTexNamingImporterModule, TexNamingImporter)