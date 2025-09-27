#include "TextureImportBridgeListener.h"

#include "Subsystems/ImportSubsystem.h"
#include "Engine/Texture.h"


void UTextureImportBridgeListener::Initialize(FOnTextureImported InOnTextureImported)
{
	OnTextureImported = InOnTextureImported;


#if WITH_EDITOR
	if (UImportSubsystem* ImportSubsystem = GEditor->GetEditorSubsystem<UImportSubsystem>())
	{
		ImportSubsystem->OnAssetPostImport.AddUObject(this, &UTextureImportBridgeListener::OnPostImport);
	}
#endif
}

void UTextureImportBridgeListener::OnPostImport(UFactory* InFactory, UObject* InCreatedObject)
{
	if (UTexture* AsTexture = Cast<UTexture>(InCreatedObject))
	{
		if (OnTextureImported.IsBound())
		{
			OnTextureImported.Execute(AsTexture);
		}
	}
}