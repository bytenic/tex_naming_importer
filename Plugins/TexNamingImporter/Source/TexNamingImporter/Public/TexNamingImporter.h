// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Modules/ModuleManager.h"

class FToolBarBuilder;
class FMenuBuilder;
class UTextureImportBridgeListener;

class FTexNamingImporterModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
	
	/** This function will be bound to Command (by default it will bring up plugin window) */
	void PluginButtonClicked();

	void HandleTexturePostImport(class UTexture* Texture);
	
	
private:
	void RegisterMenus();

	TSharedRef<class SDockTab> OnSpawnPluginTab(const class FSpawnTabArgs& SpawnTabArgs);
	/** Strong ref so the UObject listener doesn’t get GC’d */
	TStrongObjectPtr<UTextureImportBridgeListener> Listener;


	/** Absolute path to {Plugin}/Content/Python */
	FString PythonDir;


	/** Runs your python entrypoint with asset context */
	void RunPythonForTexture(class UTexture* Texture);


	/** Discover plugin’s Python directory */
	void ResolvePythonDir();


	bool RunPythonFile(const FString& ScriptFileName, const TArray<FString>& Args = {});
	

private:
	TSharedPtr<class FUICommandList> PluginCommands;
};


