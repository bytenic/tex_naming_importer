// Copyright Epic Games, Inc. All Rights Reserved.

#include "TexNamingImporterCommands.h"

#define LOCTEXT_NAMESPACE "FTexNamingImporterModule"

void FTexNamingImporterCommands::RegisterCommands()
{
	UI_COMMAND(OpenPluginWindow, "TexNamingImporter", "Bring up TexNamingImporter window", EUserInterfaceActionType::Button, FInputChord());
}

#undef LOCTEXT_NAMESPACE
