# TexNamingImporter ユーザーガイド

## 目次

- [TexNamingImporter ユーザーガイド](#texnamingimporter-ユーザーガイド)
  - [目次](#目次)
  - [概要](#概要)
  - [インストール](#インストール)
  - [セットアップ手順](#セットアップ手順)
  - [設定ファイル（設計とひな型）](#設定ファイル設計とひな型)
    - [TextureConfig.json — 種類ごとの既定値](#textureconfigjson--種類ごとの既定値)
      - [パラメータ解説（表）](#パラメータ解説表)
    - [SuffixConfig.json — サフィックス定義](#suffixconfigjson--サフィックス定義)
      - [パラメータ解説（表）](#パラメータ解説表-1)
    - [DirectoryConfig.json — 実行対象パス](#directoryconfigjson--実行対象パス)
  - [動作の仕組み（内部概要）](#動作の仕組み内部概要)
  - [トラブルシューティング](#トラブルシューティング)

---

## 概要

設定したディレクトリ配下にインポートされた `UTexture`を、設定ファイルと命名規則(サフィックス)に基づいて最適なプロパティ適用を行う Editor 用プラグインです。

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

2. **3 つの JSON を配置**
1で作成した設定ファイルを配置します。  
これらのファイルのテンプレートはこのプラグインのトップフォルダにzipファイルで配置しています
   ```
   TextureConfig.json
   SuffixConfig.json
   DirectoryConfig.json
   ```

1. **DirectorySettings.json を編集（必須）**  
   処理対象とする `/Game/...` の**ルートパス**を `run_dir` に列挙します。  
   これに含まれない場所へインポートされたテクスチャは**スキップ**されます。

2. **動作確認**  
  1で設定したディレクトリ配下にテクスチャをインポートし、以下を確認します。

   * ログに「処理開始／適用パラメータ」が出る
   * インポート後、テクスチャのプロパティが自動で反映されている

---

## 設定ファイル（設計とひな型）

> 3 つの JSON は **UTF-8** で保存してください。
> 役割は「**種類ごとの既定値**」「**サフィックス定義**」「**実行対象パス**」に分離します。

### TextureConfig.json — 種類ごとの既定値

**目的**: テクスチャ**種類**（例: `col`, `msk`, `nml`, `mat`, `cub`, `flw` …）ごとに、
**アドレスモード／圧縮／sRGB／最大解像度**を定義します。

#### パラメータ解説（表）<a id="パラメータ解説表texturesettings"></a>

> 形式：`{ "<type>": { ...パラメータ... }, ... }`（例：`"col"`, `"msk"`, `"nml"` など）

| キー                 | 型       | 設定できる値                                              | 説明                        | 備考                                    |
| ------------------ | ------- | ---------------------------------------------------- | ------------------------- | ------------------------------------- |
| `address_u`        | string  | `WRAP` / `CLAMP` / `MIRROR`                          | U 軸のデフォルトテクスチャアドレスモード          | `SuffixSettings` のアドレスサフィックスで**上書きができます。詳細はSuffixConfig.jsonを参照してください** |
| `address_v`        | string  | `WRAP` / `CLAMP` / `MIRROR`                          | V 軸のデフォルトアドレスモード               | 同上                                    |
| `address_w` *(任意)* | string  | `WRAP` / `CLAMP` / `MIRROR`                          | **3D テクスチャ**用W軸のデフォルトアドレスモード | `address_suffix_3d` がある場合に使用          |
| `max_in_game`      | number  | 0（無制限） / 256 / 512 / 1024 / 2048 / …               | **ゲーム内最大解像度**（px）     | 0 は無制限。POW2 丸めと併用推奨                   |
| `enforce_pow2`     | boolean | `true` / `false`                                     | サイズを 2 の冪に正規化（丸め）         | 非 POW2 を避けたい場合に有効                     |
| `compression`      | string  | `BC7` / `MASKS` / `NORMAL_MAP` / `HDR` / `ALPHA` / `GRAYSCALE`/ `EDITOR_ICON`/ `DISTANCE_FIELD_FONT`/  `DEFAULT` … | **圧縮設定名**           | エンジン側の列挙に準拠します                          |
| `srgb`             | string  | `ON` / `OFF` / `AUTO`                                | sRGB フラグの扱い               | `AUTO` は種類や圧縮でそれらしい値を設定しますができる限り使用しないことを推奨します。                 |
| `mip_gen`       | string | `FROM_TEXTURE_GROUP`(既定) / `NO_MIPMAPS` / `SIMPLE_AVERAGE` / `SHARPEN0`〜`SHARPEN8`                                                                                                                             | **MipGenSettings** を指定します。`FROM_TEXTURE_GROUP` は `texture_group`（LODGroup）に従います。 | 不正値は**エラー**として処理されます。   |
| `texture_group` | string | `WORLD`(既定) / `WORLD_NORMAL_MAP` / `WORLD_SPECULAR` / `CHARACTER` / `CHARACTER_NORMAL_MAP` / `CHARACTER_SPECULAR` / `UI` / `LIGHTMAP` / `SHADOWMAP` / `SKYBOX` / `VEHICLE` / `CINEMATIC` / `EFFECTS` / `MEDIA` | **LODGroup**（TextureGroup）を指定します。                   | 不正値は**エラー**として処理されます。エンジンのビルドにより利用可能なグループが異なる場合があります。 |

**設定例**

```json
{
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
    "max_in_game": 1024,
    "enforce_pow2": true,
    "compression": "MASKS",
    "srgb": "OFF",
    "mip_gen": "NO_MIPMAPS",
    "texture_group": "EFFECTS"
  },
  "nml": {
    "address_u": "WRAP",
    "address_v": "WRAP",
    "max_in_game": 1024,
    "enforce_pow2": true,
    "compression": "NORMAL_MAP",
    "srgb": "OFF",
    "mip_gen": "FROM_TEXTURE_GROUP",
    "texture_group": "WORLD"
  }
}
```

---

### SuffixConfig.json — サフィックス定義

**テクスチャ種類**（`texture_type`）、**アドレスモード**（2D: `address_suffix_2d` / 3D: `address_suffix_3d`）をテクスチャのサフィックスからします。**優先順位**は `suffix_index` で制御します。

#### パラメータ解説（表）<a id="パラメータ解説表suffixsettings"></a>

| キー                         | 型           | 設定値の例                                            |   | 説明                                    | 備考                         |
| -------------------------- | ----------- | ---------------------------------------------------------- | -------- | ------------------------------------- | -------------------------- |
| `texture_type`             | string[]    | `["col","msk","nml","mat","cub","flw"]`                    |  | **テクスチャの種類**                        | TextureConfig.jsonで設定した値をここに配置してください。        |
| `address_suffix_2d`        | object(map) | `"cc": ["CLAMP","CLAMP"]` / `"ww": ["WRAP","WRAP"]`        |  | **2D 用のアドレスサフィックスです。ここに設定した値でテクスチャのアドレスモードをインポート時に上書きします。** | 例：`"cw": ["CLAMP","WRAP"]` |
| `address_suffix_3d` *(任意)* | object(map) | `"cww": ["CLAMP","WRAP","WRAP"]`                           |  | **3D 用のアドレスサフィックスです。**。値=[U,V,W]       | 3D テクスチャを扱う場合に追加(**現在は無効にしています**)           |
| `suffix_index`             | string[]    | `["texture_type","address_suffix_2d"]` |    | **サフィックスの配置順**                           | サフィックスの順序を定義します            |

**設定例**

```json
{
  "texture_type": ["col", "msk", "nml", "mat", "cub", "flw"], //この値はTextureConfig.jsonのキーに連動しているので同じ値を設定してください。(将来的に削除予定)
  "address_suffix_2d": {
    "cc": ["CLAMP", "CLAMP"],
    "cw": ["CLAMP", "WRAP"],
    "cm": ["CLAMP", "MIRROR"],
    "wc": ["WRAP",  "CLAMP"],
    "ww": ["WRAP",  "WRAP"],
    "wm": ["WRAP",  "MIRROR"],
    "mc": ["MIRROR","CLAMP"],
    "mw": ["MIRROR","WRAP"],
    "mm": ["MIRROR","MIRROR"]
  },
  "address_suffix_3d": {
    "cww": ["CLAMP", "WRAP", "WRAP"],
    "mmc": ["MIRROR", "MIRROR", "CLAMP"]
  },
  "suffix_index": ["texture_type", "address_suffix_2d"]
}

**suffix_indexの例**  
- 有効な名前: **{Textureの名前}_col_cc** 
- 無効な名前: **{Textureの名前}_ww_nrm** 

```

---

### DirectoryConfig.json — 実行対象パス

**処理対象とする `/Game/...` のルート**を列挙します。
ここに含まれないインポートは**早期リターン（スキップ）**します。

**キー仕様**

* `run_dir` : `string[]`（先頭は `/Game` で、末尾スラッシュは任意）

**設定例**

```json
{
  "run_dir": ["/Game/VFX", "/Game/Debug"]
}
```
---

## 動作の仕組み（内部概要）

1. **StartupModule**

   * `{ProjectDir}/Config/TexNamingImporter/DirectorySettings.json` を読み込み
   * ImportSubsystem の `OnAssetPostImport` にリスナー登録
   * プラグインの Python スクリプト参照パスを解決

2. **OnAssetPostImport → HandleTexturePostImport(UTexture*)**

   * テクスチャのロングパッケージパス取得
   * **`run_dir` 配下でなければ即スキップ**
   * 対象であれば Python（例: `import_texture_event.py`）を実行し、設定ロード→検証→適用

3. **Python 側（例: `import_texture_event.py`）**

   * 引数: `TextureSettings.json` / `SuffixSettings.json` / `DirectorySettings.json` / `ObjectPath`
   * `TextureSettings` と `SuffixSettings` を合成して適用パラメータを生成
   * Unreal Python API で `UTexture` に反映し、必要に応じてアセット保存

---

## トラブルシューティング

* **何も起きない／適用されない**

  * インポート先が **`run_dir` 配下**か
  * 3 つの JSON が **`{ProjectDir}/Config/TexNamingImporter/`** にあるか
  * Editor ログに JSON パースエラーや Python 実行エラーがないか

* **サフィックス解釈エラー**

  * ログの該当ファイル名とサフィックスを確認
  * `SuffixSettings.json` のキー（`texture_type`, `address_suffix_2d/3d`）に**綴り漏れがないか**

