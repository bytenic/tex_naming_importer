#pragma once

#include "CoreMinimal.h"
#include "UObject/ObjectMacros.h"
#include "UObject/Object.h"
#include "TextureImportBridgeListener.generated.h"

DECLARE_DELEGATE_OneParam(FOnTextureImported, class UTexture*);

UCLASS()
class UTextureImportBridgeListener : public UObject
{
	GENERATED_BODY()
public:
	void Initialize(FOnTextureImported InOnTextureImported);


private:
	/** UImportSubsystem delegates */
	//UFUNCTION()
	//void OnPreImport(UObject* InParent, const FString& InName, const FString& InType, const FString& InFilename);


	UFUNCTION()
	void OnPostImport(class UFactory* InFactory, UObject* InCreatedObject);


	FOnTextureImported OnTextureImported;
};
