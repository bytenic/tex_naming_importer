# TexNamingImporter ユーザーガイド

## 目次

- [TexNamingImporter ユーザーガイド](#texnamingimporter-ユーザーガイド)
  - [目次](#目次)
  - [概要](#概要)
  - [インストール](#インストール)
  - [セットアップ手順](#セットアップ手順)
  - [設定ファイル（Config.json）](#設定ファイルconfigjson)
    - [トップレベルキー](#トップレベルキー)
    - [`texture_config` の書式](#texture_config-の書式)
    - [サフィックス関連の書式](#サフィックス関連の書式)
    - [SubUV テクスチャ向け設定](#subuv-テクスチャ向け設定)
    - [設定ファイルの例](#設定ファイルの例)
  - [トラブルシューティング](#トラブルシューティング)
  - [(エンジニア向け)動作の流れ](#エンジニア向け動作の流れ)

---

## 概要

設定したディレクトリ配下にインポートされた `UTexture` を、設定ファイルと命名規則(サフィックス)に基づいて最適なプロパティ適用を行う
Editor 用プラグインです。サフィックス検証に失敗したテクスチャは自動削除され、エラー内容はエディタのダイアログでも通知されます。

---

## インストール

1. プロジェクトの `Plugins/` 配下に **TexNamingImporter** を配置します。
2. Unreal Editor を起動し、**Edit → Plugins** から **TexNamingImporter** を有効化。
3. **Python Editor Script Plugin** を有効化。
4. Editor を再起動します。

> すでに Editor を開いている場合は、プラグイン有効化後に **エディタ再起動**が必要です。

---

## セットアップ手順

1. **設定フォルダ作成**  
   プロジェクトフォルダの以下の場所にディレクトリを作成してください。

   ```
   {Projectの場所}/Config/TexNamingImporter/
   ```

2. **Config.json を配置**  
   1 で作成したフォルダに `Config.json` を配置します。テンプレートはプラグインルートの zip に含まれています。

   ```
   {PluginDir}/Config.zip
     └ Config.json
   ```

3. **Config.json を編集（必須）**  
   - 処理対象とする `/Game/...` の**ルートパス**を `run_dir` に列挙します。
   - サフィックスや種類ごとの設定を後述のフォーマットに従って記述します。
   - ここに含まれない場所へインポートされたテクスチャは**スキップ**されます。

4. **動作確認**  
   3 で設定したディレクトリ配下にテクスチャをインポートし、以下を確認します。

   * ログに「処理開始／適用パラメータ／削除結果」が出る
   * サフィックス誤りがあるテクスチャは削除され、エディタにダイアログが表示される
   * 正常なテクスチャではプロパティが自動で反映されている

---

## 設定ファイル（Config.json）

> `Config.json` は **UTF-8** で保存してください。

### トップレベルキー

| キー | 型 | 説明 |
| ---- | --- | --- |
| `run_dir` | string[] | 処理対象とする `/Game/...` のルートパス一覧。ここに含まれないインポートはスキップされます。 |
| `address_suffix_2d` | object | `{ サフィックス: [U, V] }` の形で 2D アドレスモードを上書き。値は `WRAP` / `CLAMP` / `MIRROR` など。 |
| `address_suffix_3d` *(任意)* | object | `{ サフィックス: [U, V, W] }` の形で 3D アドレスモードを上書き。3D テクスチャを扱うときに使用。 |
| `texture_config` | object | テクスチャ種類ごとの既定設定。詳細は下記「texture_config の書式」を参照。 |
| `texture_type` | string[] | サフィックス判定に使用するテクスチャ種類。基本的に`texture_config` のキーをそのまま記載してください。一部のtexture_configを無効につつconfigファイル状に残したい場合はここに使用するtexture_configのキーを指定することで使用するテクスチャの種類を制限できます |
| `suffix_index` | string[] | サフィックス順序のルール指定。例: `["texture_type", "address_suffix_2d"]`の場合 : `textureの名前_{texture_typeの種類}_{address_suffix_2dのキー}`がサフィックスのルールとなります |
| `enable_subuv_texture_override` *(任意)* | boolean | `true` で SubUV テクスチャ検知を有効化。`4x4` など `NxM` トークンが含まれる場合、`subuv_max_in_game` で上書き。 |
| `subuv_max_in_game` *(任意)* | number | SubUV 検知時に使用する最大解像度。数値を入力してください / `2048` など。 |

### `texture_config` の書式

> 形式：`texture_config.{種類名} = { ...パラメータ... }`（例：`"col"`, `"msk"`, `"nml"` など）

| キー | 型 | 設定できる値 | 説明 | 備考 |
| ---- | --- | --- | --- | --- |
| `address_u` / `address_v` / `address_z` *(任意)* | string | `WRAP` / `CLAMP` / `MIRROR` | テクスチャアドレスモード（U/V/W）。`address_suffix_*` で上書き可能。 | 3D テクスチャは `address_z` を利用。 |
| `max_in_game` | number/string  | 0（無制限） / 256 / 512 / … / `"AUTO"` / | ゲーム内最大解像度（px）。 | `0` または `"AUTO"` は無制限扱い。 |
| `enforce_pow2` | boolean | `true` / `false` | サイズを 2 の冪に正規化（丸め）。 |  |
| `compression` | string | `BC7` / `MASKS` / `NORMAL_MAP` / `HDR` / `ALPHA` / `GRAYSCALE` / `EDITOR_ICON` / `DISTANCE_FIELD_FONT` / `DEFAULT` など | 圧縮設定名。 | Unreal Engine の列挙値に準拠。 |
| `srgb` | string | `ON` / `OFF` / `AUTO` | sRGB フラグの扱い。 | `AUTO` は設定推測。可能なら明示指定を推奨。 |
| `mip_gen` | string | `FROM_TEXTURE_GROUP` / `NO_MIPMAPS` / `SIMPLE_AVERAGE` / `SHARPEN0`〜`SHARPEN8` | `TextureMipGenSettings` の指定。 | 無効値はエラー。 |
| `texture_group` | string | `WORLD` / `WORLD_NORMAL_MAP` / `WORLD_SPECULAR` / `CHARACTER` / `CHARACTER_NORMAL_MAP` / `CHARACTER_SPECULAR` / `UI` / `LIGHTMAP` / `SHADOWMAP` / `SKYBOX` / `VEHICLE` / `CINEMATIC` / `EFFECTS` / `MEDIA` など | `TextureGroup` の指定。 | エンジンビルドにより利用可能なグループが異なる場合があります。 |

### サフィックス関連の書式

* `texture_type` はテクスチャ種別を列挙します。例: `"col"`, `"msk"`, `"nml"` など。
* `suffix_index` でサフィックスの読み取り順を定義します。例: `[{Texture名}_{texture_type}_{address_suffix_2d}]` の順。
* `address_suffix_2d` / `address_suffix_3d` にサフィックス→アドレスモードを記述します。

**suffix_index の例**

- 有効な名前: **{Texture名}_col_cc**
- 無効な名前: **{Texture名}_ww_nrm**（`suffix_index` に沿っていない）

### SubUV テクスチャ向け設定

* `enable_subuv_texture_override` を `true` にすると、サフィックスやファイル名に `4x4` など `NxM` 形式のトークンが含まれるテクスチャを SubUV とみなします。
* SubUV と判定された場合、`subuv_max_in_game` の値で `max_in_game` を上書きします。

### 設定ファイルの例

```json
{
  "run_dir": ["/Game/VFX", "/Game/Debug"],
  "texture_type": ["col", "msk", "nml", "mat", "cub", "flw"],
  "suffix_index": ["texture_type", "address_suffix_2d"],
  "address_suffix_2d": {
    "cc": ["CLAMP", "CLAMP"],
    "cw": ["CLAMP", "WRAP"],
    "wc": ["WRAP", "CLAMP"],
    "ww": ["WRAP", "WRAP"]
  },
  "texture_config": {
    "col": {
      "address_u": "WRAP",
      "address_v": "WRAP",
      "max_in_game": 1024,
      "enforce_pow2": true,
      "compression": "BC7",
      "srgb": "ON",
      "mip_gen": "FROM_TEXTURE_GROUP",
      "texture_group": "EFFECTS"
    },
    "msk": {
      "address_u": "CLAMP",
      "address_v": "CLAMP",
      "max_in_game": 512,
      "compression": "MASKS",
      "srgb": "OFF",
      "mip_gen": "NO_MIPMAPS",
      "texture_group": "EFFECTS"
    },
    "nml": {
      "address_u": "WRAP",
      "address_v": "WRAP",
      "max_in_game": "P1024",
      "compression": "NORMAL_MAP",
      "srgb": "OFF",
      "texture_group": "WORLD"
    }
  },
  "enable_subuv_texture_override": true,
  "subuv_max_in_game": 256
}
```

---

## トラブルシューティング

* **何も起きない／適用されない**

  * インポート先が **`run_dir` 配下**か
  * `Config.json` が **`{ProjectDir}/Config/TexNamingImporter/`** にあり、JSON が正しく記述されているか
  * Editor ログに JSON パースエラーや Python 実行エラーがないか

* **サフィックス解釈エラー**

  * ログおよび表示されたダイアログで該当ファイル名とサフィックスを確認
  * `Config.json` の `texture_type` / `address_suffix_2d` / `address_suffix_3d` に**綴り漏れがないか**
  * 誤ったサフィックスのテクスチャは自動削除されるため、必要に応じてソースファイルから再インポートしてください

---

## (エンジニア向け)動作の流れ

1. **StartupModule(c++)**

   * `{ProjectDir}/Config/TexNamingImporter/Config.json` を読み込み
   * ImportSubsystem の `OnAssetPostImport` にリスナー登録
   * プラグインの Python スクリプト参照パスを解決

2. **テクスチャインポート時: OnAssetPostImport → HandleTexturePostImport(c++)**

   * テクスチャのロングパッケージパス取得
   * **`run_dir` 配下でなければ即スキップ**
   * 対象であれば Python（`texture_configurator.py`）を `--delete --dialog` 引数付きで実行し、設定ロード→検証→適用

3. **プロパティ適用（`texture_configurator.py`）**

   * 引数: `Config.json` / `ObjectPath` / `--delete` / `--dialog`
   * `Config.json` を読み込み、サフィックス検証と種類ごとのパラメータ生成を実施
   * Unreal Python API で `UTexture` に反映し、サフィックスエラー時は削除、エラーがあればダイアログ表示

