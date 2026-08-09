# mise-darwin

`tacogips/nix` の macOS（nix-darwin / Home Manager）構成を、mise を入口に
再構築するリポジトリです。Nix Store や nix-darwin の世代管理には依存しません。

## 構成

```text
mise.toml                    共通ツール・環境変数・タスク
mise.macos-arm64.toml        Apple Silicon Mac 共通パッケージ・defaults・dotfiles
mise.desktop.toml            taco-mac の GUI アプリ・MAS アプリ
mise.home-server.toml        darwin-mac-home-server のサービス依存
dotfiles/.config/nvim/       通常の Lua + lazy.nvim 構成
home-server/                 /etc に収束させるサーバーテンプレート
scripts/                     冪等な補助処理・検証・Nix アンインストール
Brewfile.*                   Cask と third-party tap の差分
```

`mise.macos-arm64.toml` とホストプロファイルを同時に明示して実行します。
`bootstrap` wrapper はこの指定を行うため、通常は `-E` を直接扱う必要はありません。

## Bootstrap

Homebrew と mise の導入後、次を実行します。

```sh
git clone https://github.com/tacogips/mise-darwin ~/gits/tacogips/mise-darwin
cd ~/gits/tacogips/mise-darwin
mise trust
./bootstrap desktop
```

home server は次の通りです。

```sh
./bootstrap home-server
```

変更を適用せず確認する場合:

```sh
mise -E macos-arm64 -E desktop bootstrap --dry-run
mise -E macos-arm64 -E desktop bootstrap status --missing
```

既存の Home Manager symlink と衝突した場合、bootstrap は上書きせず停止します。
内容を確認して退避した後に限り、`--force-dotfiles` を指定してください。

```sh
mise -E macos-arm64 -E desktop bootstrap --yes --force-dotfiles
```

## Neovim

Neovim は `dotfile_nvim` の階層構成と NVF の現行設定を元に、次の単位へ分割
しています。

```text
dotfiles/.config/nvim/
├── init.lua
├── ftplugin/
└── lua/taco/
    ├── core/       options・keymaps・autocmds
    └── plugins/    editor/UI/LSP・completion
```

プラグインは初回起動時に `lazy.nvim` が導入します。LSP、formatter、CLI は
mise の tools または bootstrap の Homebrew package として管理します。
`lazy-lock.json` が生成されたら Git に追加し、プラグインも固定してください。

## 検証と Nix の削除

まず新しい shell で検証します。

```sh
mise -E macos-arm64 -E desktop run verify
```

問題がないことを確認してから、Nix を削除します。自動削除は Determinate
installer の uninstall receipt がある場合だけ実行し、legacy installer は安全の
ため停止して元の installer に対応する手順を要求します。

```sh
mise run nix:uninstall -- --confirm
```

Nix の削除は不可逆です。`tacogips/nix` は移行完了まで参照用に残し、この
リポジトリの検証が通ってから削除してください。

## 現時点の境界

- mise bootstrap は逐次収束で、nix-darwin の atomic switch / rollback はありません。
- Formula は mise の direct brew manager、Cask と API metadata のない third-party tap は Homebrew Bundle で収束します。既存 Homebrew cask の receipt と競合しないための分離です。
- Mac App Store は Apple Account、Xcode は初回起動・license 同意が必要な場合があります。
- system LaunchDaemon は必要になった時点で、確認可能な専用 task と plist を追加します。
- home server の `/etc` と volume directory は `home-server:apply` task が sudo で収束します。
