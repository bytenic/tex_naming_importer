// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Framework/Commands/Commands.h"
#include "TexNamingImporterStyle.h"

class FTexNamingImporterCommands : public TCommands<FTexNamingImporterCommands>
{
public:

	FTexNamingImporterCommands()
		: TCommands<FTexNamingImporterCommands>(TEXT("TexNamingImporter"), NSLOCTEXT("Contexts", "TexNamingImporter", "TexNamingImporter Plugin"), NAME_None, FTexNamingImporterStyle::GetStyleSetName())
	{
	}

	// TCommands<> interface
	virtual void RegisterCommands() override;

public:
	TSharedPtr< FUICommandInfo > OpenPluginWindow;
};