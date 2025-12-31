---
marp: true
theme: default
class: invert
---

# Textureのプロパティ設定ツールを作った話

---
# アジェンダ
- ## 作ったもの紹介
- ## Pythonでつくるメリット
---

# 作ったもの紹介

---
## テクスチャの設定をインポート時に自動で設定できるツール
設定できるもの
- アドレス設定
- ゲーム中の最大解像度
- 2の累乗の強制フラグ
- 圧縮フォーマット
- sRGBフラグ
- Mip設定
- テクスチャグループ
- SubUV使用時の最大解像度
---
## 設定の適用はテクスチャファイル名のサフィックスから

---
## 設定はjsonファイルに記載
```
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
            "address_u": "WRAP", 
            "address_v": "WRAP", 
            "max_in_game": 1024, 
            "enforce_pow2": true, 
            "compression": "ALPHA", 
            "srgb": "OFF", 
            "mip_gen": "NO_MIPMAPS", 
            "texture_group": "EFFECTS"
        }
   }
```

---

## 

--- 

# Pythonで作ったメリット

---

## C++を使わなくて良い
- コンパイル不要
- Editorがクラッシュしない

--- 
## 外部のユニットテストツールが使える
- このツールの処理の半分以上は文字列処理
- Unrealのモジュールが不要
- Unreal依存の処理と非依存の処理を分離することで軽量なテストが書ける！
---

## 別エンジンの載せ替えが容易になる(その気になれば)

---

## AIがフルで使える
- ツールの8割、9割をAIで実装
- C++
  - AI: 〇
  - コンパイル: ×
- Blueprint
  - AI: ×
  - コンパイル: 〇
- Unreal Python
  - AI: 〇
  - コンパイル: 〇 

---
