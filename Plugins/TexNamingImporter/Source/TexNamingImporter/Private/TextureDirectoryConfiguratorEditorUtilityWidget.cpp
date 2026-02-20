#include "TextureDirectoryConfiguratorEditorUtilityWidget.h"

#include "IPythonScriptPlugin.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/MessageDialog.h"
#include "Misc/Paths.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

void UTexDirCfgEUWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (ConfigPath.TrimStartAndEnd().IsEmpty())
	{
		ConfigPath = GetDefaultConfigPath();
	}

	if (DirectoryPath.TrimStartAndEnd().IsEmpty())
	{
		DirectoryPath = TEXT("/Game");
	}

	SyncUiFromArguments();
}

TSharedRef<SWidget> UTexDirCfgEUWidget::RebuildWidget()
{
	TSharedRef<SWidget> Root = SNew(SBorder)
		.Padding(12.0f)
		[
			SNew(SVerticalBox)

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 0.0f, 0.0f, 6.0f)
			[
				SNew(STextBlock)
				.Text(FText::FromString(TEXT("Config")))
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 0.0f, 0.0f, 10.0f)
			[
				SAssignNew(ConfigPathTextBox, SEditableTextBox)
				.MinDesiredWidth(700.0f)
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 0.0f, 0.0f, 6.0f)
			[
				SNew(STextBlock)
				.Text(FText::FromString(TEXT("Execute Dir")))
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 0.0f, 0.0f, 10.0f)
			[
				SAssignNew(DirectoryPathTextBox, SEditableTextBox)
				.MinDesiredWidth(700.0f)
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 0.0f, 0.0f, 6.0f)
			[
				SAssignNew(DeleteCheckBox, SCheckBox)
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("--delete (サフィックスエラーがある場合テクスチャを削除)")))
				]
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 0.0f, 0.0f, 6.0f)
			[
				SAssignNew(DialogCheckBox, SCheckBox)
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("--dialog (実行中にエラーダイアログを表示)")))
				]
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 0.0f, 0.0f, 12.0f)
			[
				SAssignNew(NonRecursiveCheckBox, SCheckBox)
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("--non-recursive (指定ディレクトリ直下のテクスチャのみ実行)")))
				]
			]

			+ SVerticalBox::Slot()
			.AutoHeight()
			.HAlign(HAlign_Right)
			[
				SNew(SHorizontalBox)

				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(0.0f, 0.0f, 8.0f, 0.0f)
				[
					SNew(SButton)
					.Text(FText::FromString(TEXT("Reset")))
					.OnClicked_Lambda([this]()
					{
						return HandleResetClicked();
					})
				]

				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(SButton)
					.Text(FText::FromString(TEXT("Run")))
					.OnClicked_Lambda([this]()
					{
						return HandleRunClicked();
					})
				]
			]
		];

	SyncUiFromArguments();

	return Root;
}

FReply UTexDirCfgEUWidget::HandleRunClicked()
{
	SyncArgumentsFromUi();
	RunTextureDirectoryConfigurator();
	return FReply::Handled();
}

FReply UTexDirCfgEUWidget::HandleResetClicked()
{
	ResetToDefaultArguments();
	SyncUiFromArguments();
	return FReply::Handled();
}

void UTexDirCfgEUWidget::SyncUiFromArguments()
{
	if (ConfigPathTextBox.IsValid())
	{
		ConfigPathTextBox->SetText(FText::FromString(ConfigPath));
	}
	if (DirectoryPathTextBox.IsValid())
	{
		DirectoryPathTextBox->SetText(FText::FromString(DirectoryPath));
	}
	if (DeleteCheckBox.IsValid())
	{
		bDeleteOnSuffixError = DeleteCheckBox->IsChecked();
	}
	if (DialogCheckBox.IsValid())
	{
		bShowDialogOnError = DialogCheckBox->IsChecked();
	}
	if (NonRecursiveCheckBox.IsValid())
	{
		bNonRecursive = NonRecursiveCheckBox->IsChecked();
	}
}

void UTexDirCfgEUWidget::SyncArgumentsFromUi()
{
	if (ConfigPathTextBox.IsValid())
	{
		ConfigPath = ConfigPathTextBox->GetText().ToString().TrimStartAndEnd();
	}
	if (DirectoryPathTextBox.IsValid())
	{
		DirectoryPath = DirectoryPathTextBox->GetText().ToString().TrimStartAndEnd();
	}
	if (DeleteCheckBox.IsValid())
	{
		bDeleteOnSuffixError = DeleteCheckBox->IsChecked();
	}
	if (DialogCheckBox.IsValid())
	{
		bShowDialogOnError = DialogCheckBox->IsChecked();
	}
	if (NonRecursiveCheckBox.IsValid())
	{
		bNonRecursive = NonRecursiveCheckBox->IsChecked();
	}
}

FString UTexDirCfgEUWidget::GetDefaultConfigPath() const
{
	return FPaths::Combine(
		FPaths::ProjectConfigDir(),
		TEXT("TexNamingImporter"),
		TEXT("Config.json"));
}

FString UTexDirCfgEUWidget::PyEscape(const FString& In)
{
	FString Out = In;
	Out.ReplaceInline(TEXT("\\"), TEXT("\\\\"), ESearchCase::CaseSensitive);
	Out.ReplaceInline(TEXT("'"), TEXT("\\'"), ESearchCase::CaseSensitive);
	return Out;
}

void UTexDirCfgEUWidget::ResetToDefaultArguments()
{
	ConfigPath = GetDefaultConfigPath();
	DirectoryPath = TEXT("/Game");
	bDeleteOnSuffixError = false;
	bShowDialogOnError = false;
	bNonRecursive = false;
}

bool UTexDirCfgEUWidget::RunTextureDirectoryConfigurator()
{
	FString LocalConfigPath = ConfigPath.TrimStartAndEnd();
	if (LocalConfigPath.IsEmpty())
	{
		LocalConfigPath = GetDefaultConfigPath();
	}

	FString LocalDirectoryPath = DirectoryPath.TrimStartAndEnd();
	if (LocalDirectoryPath.IsEmpty())
	{
		FMessageDialog::Open(EAppMsgType::Ok, FText::FromString(TEXT("dir_path is required.")));
		return false;
	}

	if (!LocalDirectoryPath.StartsWith(TEXT("/")))
	{
		LocalDirectoryPath = TEXT("/") + LocalDirectoryPath;
	}

	TArray<FString> Args;
	Args.Reserve(5);
	Args.Add(LocalConfigPath);
	Args.Add(LocalDirectoryPath);
	if (bDeleteOnSuffixError)
	{
		Args.Add(TEXT("--delete"));
	}
	if (bShowDialogOnError)
	{
		Args.Add(TEXT("--dialog"));
	}
	if (bNonRecursive)
	{
		Args.Add(TEXT("--non-recursive"));
	}

	if (!RunPythonFile(TEXT("texture_directory_configurator.py"), Args))
	{
		FMessageDialog::Open(
			EAppMsgType::Ok,
			FText::FromString(TEXT("Failed to run texture_directory_configurator.py. Check Output Log for details.")));
		return false;
	}

	return true;
}

bool UTexDirCfgEUWidget::RunPythonFile(
	const FString& ScriptFileName,
	const TArray<FString>& Args) const
{
	if (IPythonScriptPlugin::Get() == nullptr)
	{
		UE_LOG(LogTemp, Error, TEXT("PythonScriptPlugin is not available."));
		return false;
	}

	FString PluginBaseDir;
	const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("TexNamingImporter"));
	if (Plugin.IsValid())
	{
		PluginBaseDir = Plugin->GetBaseDir();
	}
	else
	{
		PluginBaseDir = FPaths::Combine(FPaths::ProjectDir(), TEXT("Plugins"), TEXT("TexNamingImporter"));
	}

	FString AbsPyFile = FPaths::Combine(
		PluginBaseDir,
		TEXT("Content"),
		TEXT("Python"),
		ScriptFileName);
	AbsPyFile = FPaths::ConvertRelativePathToFull(AbsPyFile);
	FPaths::MakeStandardFilename(AbsPyFile);

	if (!FPaths::FileExists(AbsPyFile))
	{
		UE_LOG(LogTemp, Error, TEXT("Python file not found: %s"), *AbsPyFile);
		return false;
	}

	FString ImportDirAbs = FPaths::GetPath(AbsPyFile);
	FPaths::ConvertRelativePathToFull(ImportDirAbs);
	FPaths::MakeStandardFilename(ImportDirAbs);

	const FString EscFile = PyEscape(AbsPyFile);
	const FString EscImportDir = PyEscape(ImportDirAbs);

	TStringBuilder<1024> CommandBuilder;
	CommandBuilder.Append(TEXT("import sys, runpy\n"));
	CommandBuilder.Appendf(TEXT("sys.path.insert(0, '%s')\n"), *EscImportDir);
	CommandBuilder.Append(TEXT("sys_argv_backup = list(sys.argv)\n"));
	CommandBuilder.Append(TEXT("try:\n"));
	CommandBuilder.Appendf(TEXT("    sys.argv = ['%s'"), *EscFile);
	for (const FString& Arg : Args)
	{
		const FString EscArg = PyEscape(Arg);
		CommandBuilder.Appendf(TEXT(", '%s'"), *EscArg);
	}
	CommandBuilder.Append(TEXT("]\n"));
	CommandBuilder.Appendf(TEXT("    runpy.run_path('%s', run_name='__main__')\n"), *EscFile);
	CommandBuilder.Append(TEXT("finally:\n"));
	CommandBuilder.Append(TEXT("    sys.argv = sys_argv_backup\n"));
	CommandBuilder.Append(TEXT("    try:\n"));
	CommandBuilder.Appendf(TEXT("        if sys.path and sys.path[0] == '%s':\n"), *EscImportDir);
	CommandBuilder.Append(TEXT("            del sys.path[0]\n"));
	CommandBuilder.Append(TEXT("    except Exception:\n"));
	CommandBuilder.Append(TEXT("        pass\n"));

	return IPythonScriptPlugin::Get()->ExecPythonCommand(CommandBuilder.ToString());
}
