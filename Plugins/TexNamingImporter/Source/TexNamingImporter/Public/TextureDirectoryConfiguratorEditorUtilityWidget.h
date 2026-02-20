#pragma once

#include "CoreMinimal.h"
#include "EditorUtilityWidget.h"
#include "TextureDirectoryConfiguratorEditorUtilityWidget.generated.h"

class SCheckBox;
class SEditableTextBox;
class SWidget;
class FReply;

UCLASS(BlueprintType)
class TEXNAMINGIMPORTER_API UTexDirCfgEUWidget : public UEditorUtilityWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Texture Directory Configurator")
	FString ConfigPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Texture Directory Configurator")
	FString DirectoryPath = TEXT("/Game");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Texture Directory Configurator")
	bool bDeleteOnSuffixError = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Texture Directory Configurator")
	bool bShowDialogOnError = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Texture Directory Configurator")
	bool bNonRecursive = false;

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Texture Directory Configurator")
	bool RunTextureDirectoryConfigurator();

	UFUNCTION(BlueprintCallable, Category = "Texture Directory Configurator")
	void ResetToDefaultArguments();

	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeConstruct() override;

private:
	bool RunPythonFile(const FString& ScriptFileName, const TArray<FString>& Args) const;
	FString GetDefaultConfigPath() const;
	static FString PyEscape(const FString& In);

	FReply HandleRunClicked();
	FReply HandleResetClicked();
	void SyncUiFromArguments();
	void SyncArgumentsFromUi();

	TSharedPtr<SEditableTextBox> ConfigPathTextBox;
	TSharedPtr<SEditableTextBox> DirectoryPathTextBox;
	TSharedPtr<SCheckBox> DeleteCheckBox;
	TSharedPtr<SCheckBox> DialogCheckBox;
	TSharedPtr<SCheckBox> NonRecursiveCheckBox;
};
