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

	/** Runs your python entrypoint with asset context */
	void RunPythonForTexture(class UTexture* Texture);

	/** 設定のロード */
	void LoadDirectorySettings();

	/** /Game 形式のパッケージパスが run_dir 配下かどうか */
	bool IsUnderRunDir(const FString& LongPackagePath) const;

	/** Discover plugin’s Python directory */
	void ResolvePythonDir();
	
	bool RunPythonFile(const FString& ScriptFileName, const TArray<FString>& Args = {});

private:
	/** 設定ファイルのフルパス */
	FString ConfigFilePath;
	/** 許可ディレクトリ（/Game/… のロングパッケージパス。末尾スラッシュ無しで保持） */
	TArray<FString> RunDirs;
	TSharedRef<class SDockTab> OnSpawnPluginTab(const class FSpawnTabArgs& SpawnTabArgs);
	/** Strong ref so the UObject listener doesn’t get GC’d */
	TStrongObjectPtr<UTextureImportBridgeListener> Listener;
	/** Absolute path to {Plugin}/Content/Python */
	FString PythonDir;
	TSharedPtr<class FUICommandList> PluginCommands;
};


