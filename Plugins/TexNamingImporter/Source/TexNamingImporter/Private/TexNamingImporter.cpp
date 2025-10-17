// Copyright Epic Games, Inc. All Rights Reserved.

#include "TexNamingImporter.h"
#include "TexNamingImporterStyle.h"
#include "TexNamingImporterCommands.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "ToolMenus.h"
#include "Interfaces/IPluginManager.h"

#include "Editor.h"
#include "IPythonScriptPlugin.h"
#include "Subsystems/ImportSubsystem.h"
#include "Misc/Paths.h"
#include "Engine/Texture.h"

#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"

#include "TextureImportBridgeListener.h"

static const FName TexNamingImporterTabName("TexNamingImporter");

#define LOCTEXT_NAMESPACE "FTexNamingImporterModule"

void FTexNamingImporterModule::StartupModule()
{
	// {ProjectDir}/Config/TexNamingImporter/DirectoryConfig.json
	ConfigFilePath = FPaths::Combine(
		FPaths::ProjectConfigDir(),
		TEXT("TexNamingImporter"),
		TEXT("Config.json"));

	LoadDirectorySettings();
	
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

	ResolvePythonDir();
	
	Listener = TStrongObjectPtr<UTextureImportBridgeListener>(NewObject<UTextureImportBridgeListener>());
	Listener->Initialize(FOnTextureImported::CreateRaw(this, &FTexNamingImporterModule::HandleTexturePostImport));
	
}

void FTexNamingImporterModule::ShutdownModule()
{
#if WITH_EDITOR
	if (GEditor)
	{
		if (UImportSubsystem* S = GEditor->GetEditorSubsystem<UImportSubsystem>())
		{
			S->OnAssetPostImport.RemoveAll(Listener.Get());
		}
	}
#endif
	
	if (Listener.IsValid())
	{
		//Listener->RemoveFromRoot();
		Listener.Reset();
	}
	
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

void FTexNamingImporterModule::LoadDirectorySettings()
{
	RunDirs.Reset();

	if (!FPaths::FileExists(ConfigFilePath))
	{
		UE_LOG(LogTemp, Warning, TEXT("Config.json not found: %s"), *ConfigFilePath);
		return;
	}

	FString JsonText;
	if (!FFileHelper::LoadFileToString(JsonText, *ConfigFilePath))
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to read DirectorySettings.json: %s"), *ConfigFilePath);
		return;
	}

	TSharedPtr<FJsonObject> RootObj;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
	if (!FJsonSerializer::Deserialize(Reader, RootObj) || !RootObj.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to parse Config.json: %s"), *ConfigFilePath);
		return;
	}

	const TArray<TSharedPtr<FJsonValue>>* RunDirArray = nullptr;
	if (!RootObj->TryGetArrayField(TEXT("run_dir"), RunDirArray))
	{
		UE_LOG(LogTemp, Warning, TEXT("Field 'run_dir' not found in Config.json: %s"), *ConfigFilePath);
		return;
	}

	for (const TSharedPtr<FJsonValue>& Val : *RunDirArray)
	{
		FString Dir;
		if (!Val.IsValid() || !Val->TryGetString(Dir))
		{
			continue;
		}

		// 正規化：末尾スラッシュ除去、空白除去
		Dir.TrimStartAndEndInline();

		// 期待形式は "/Game/..." （ロングパッケージパス）
		// 念のため末尾のスラッシュを取り除いた同形式で保持
		if (Dir.EndsWith(TEXT("/")))
		{
			Dir.LeftChopInline(1);
		}

		if (!Dir.IsEmpty())
		{
			RunDirs.AddUnique(Dir);
		}
	}

	UE_LOG(LogTemp, Log, TEXT("Loaded %d run_dir entries"), RunDirs.Num());
}

bool FTexNamingImporterModule::IsUnderRunDir(const FString& LongPackagePath) const
{
	// LongPackagePath 例: "/Game/VFX/Textures"
	// RunDirs 例: "/Game/VFX", "/Game/Debug"

	if (LongPackagePath.IsEmpty() || RunDirs.Num() == 0)
	{
		return false;
	}

	for (const FString& Root : RunDirs)
	{
		// 同一 or 配下のときに真
		if (LongPackagePath.Equals(Root, ESearchCase::IgnoreCase))
		{
			return true;
		}
		if (LongPackagePath.StartsWith(Root + TEXT("/"), ESearchCase::IgnoreCase))
		{
			return true;
		}
	}
	return false;
}

void FTexNamingImporterModule::RunPythonForTexture(class UTexture* Texture)
{
	if (!ensure(Texture))
		return;
	
	
	// Compose a Python one-liner to set cwd/sys.path and call your module function
	const FString ObjectPath = Texture->GetPathName();
	if (IPythonScriptPlugin::Get() != nullptr)
	{
		const bool bOk = RunPythonFile(TEXT("texture_configurator.py"),
	{
				FString::Format(TEXT("{0}"), {FStringFormatArg(ConfigFilePath)}),
				FString::Format(TEXT("{0}"), {FStringFormatArg(ObjectPath)}),
				TEXT("--delete"), //suffixエラー時に削除するオプション引数
				TEXT("--dialog") //エラー時にダイアログを表示するオプション引数
			});
		if (!bOk)
		{
			UE_LOG(LogTemp, Warning, TEXT("Python execution failed for %s"), *ObjectPath);
		}
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("PythonScriptPlugin not available. Enable it in your .uplugin"));
	}
}

void FTexNamingImporterModule::ResolvePythonDir()
{
	// Find this plugin’s base dir
	FString PluginName = TEXT("TexNamingImporter"); // ← replace with your actual plugin dir name
	const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(PluginName);
	if (Plugin.IsValid())
	{
		const FString BaseDir = Plugin->GetBaseDir();
		PythonDir = FPaths::ConvertRelativePathToFull(FPaths::Combine(BaseDir, TEXT("Content"), TEXT("Python")));
	}
	else
	{
		// Fallback to project path (rare)
		PythonDir = FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), TEXT("Plugins"), PluginName, TEXT("Content"), TEXT("Python")));
	}
}


static FString PyEscape(const FString& In)
{
	// 順序が重要: まず \ を \\ にしてから ' を \'
	FString Out = In;
	Out.ReplaceInline(TEXT("\\"), TEXT("\\\\"), ESearchCase::CaseSensitive);
	Out.ReplaceInline(TEXT("'"),  TEXT("\\'"),   ESearchCase::CaseSensitive);
	return Out;
}

static bool ExecPythonFile_NoCwdChange(const FString& AbsPyFile,
                                       const TArray<FString>& Args = {},
                                       const FString& ImportDirAbs_Optional = TEXT(""))
{
    if (!IPythonScriptPlugin::Get())
    {
        UE_LOG(LogTemp, Error, TEXT("PythonScriptPlugin is not available."));
        return false;
    }

    // 絶対パス & スラッシュ統一
    FString FileAbs = AbsPyFile;
    FPaths::ConvertRelativePathToFull(FileAbs);
    FPaths::MakeStandardFilename(FileAbs); // 例: E:\a\b\c.py → E:/a/b/c.py

    // import 解決用のディレクトリ（未指定ならファイルのあるディレクトリ）
    FString ImportDirAbs = ImportDirAbs_Optional.IsEmpty() ? FPaths::GetPath(FileAbs) : ImportDirAbs_Optional;
    FPaths::ConvertRelativePathToFull(ImportDirAbs);
    FPaths::MakeStandardFilename(ImportDirAbs);

    const FString EscFile   = PyEscape(FileAbs);
    const FString EscImpDir = PyEscape(ImportDirAbs);

    // Python コマンドを 1 バッファで構築
    TStringBuilder<512> SB;
    SB.Append(TEXT("import sys, runpy\n"));
    SB.Appendf(TEXT("sys.path.insert(0, '%s')\n"), *EscImpDir); // 一時前置

    SB.Append(TEXT("sys_argv_backup = list(sys.argv)\n"));
    SB.Append(TEXT("try:\n"));
    SB.Appendf(TEXT("    sys.argv = ['%s'"), *EscFile);
    for (const FString& A : Args)
    {
        const FString EscA = PyEscape(A);
        SB.Appendf(TEXT(", '%s'"), *EscA);
    }
    SB.Append(TEXT("]\n"));
    SB.Appendf    (TEXT("    runpy.run_path('%s', run_name='__main__')\n"), *EscFile);
    SB.Append(TEXT("finally:\n"));
    SB.Append(TEXT("    sys.argv = sys_argv_backup\n"));
    SB.Append(TEXT("    try:\n"));
    SB.Appendf    (TEXT("        if sys.path and sys.path[0] == '%s':\n"), *EscImpDir);
    SB.Append(TEXT("            del sys.path[0]\n"));
    SB.Append(TEXT("    except Exception:\n"));
    SB.Append(TEXT("        pass\n"));

    // UTF-8 で実行（日本語パス対策）
    //FTCHARToUTF8 CmdUtf8(*FStringView(SB.ToView()));
    return IPythonScriptPlugin::Get()->ExecPythonCommand(SB.ToString());
}


bool FTexNamingImporterModule::RunPythonFile(const FString& ScriptFileName, const TArray<FString>& Args)
{
	const FString AbsPyFile = FPaths::ConvertRelativePathToFull(
	 FPaths::Combine(FPaths::ProjectDir(), TEXT("Plugins"), TEXT("TexNamingImporter"), TEXT("Content"), TEXT("Python"), ScriptFileName));

	if (!FPaths::FileExists(AbsPyFile))
	{
		UE_LOG(LogTemp, Error, TEXT("Python file not found: %s"), *AbsPyFile);
		return false;
	}

	// import 解決はファイルのあるディレクトリを前置（= Content/Python/）
	const FString ImportDir = FPaths::GetPath(AbsPyFile);
	return ExecPythonFile_NoCwdChange(AbsPyFile, Args, ImportDir);
	
}

void FTexNamingImporterModule::PluginButtonClicked()
{
	FGlobalTabmanager::Get()->TryInvokeTab(TexNamingImporterTabName);
}

void FTexNamingImporterModule::HandleTexturePostImport(class UTexture* Texture)
{
	if (!Texture)
	{
		return;
	}
	const FString PackageName = Texture->GetPathName();
	const FString LongPackagePath = FPackageName::GetLongPackagePath(PackageName);

	// 設定された run_dir 配下かチェック
	if (!IsUnderRunDir(LongPackagePath))
	{
		// 異なる場所にインポートされた場合は早期リターン
		UE_LOG(LogTemp, Verbose, TEXT("Skip: %s is not under run_dir (path=%s)"),
			*PackageName, *LongPackagePath);
		return;
	}
	
	RunPythonForTexture(Texture);
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