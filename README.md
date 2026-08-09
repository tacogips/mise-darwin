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
dotfiles/.agents/skills/     Apple Gateway の user skill 群
agent-user-scope/            Claude・Codex・Cursor・Riela の user-scope資産
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

Yazi の Git plugin と Gruvbox flavor は `package.toml` で固定し、bootstrap
終盤の `ya pkg install` で導入します。Karabiner は旧 Home Manager が生成していた
ANSI/Kana 記号変換を含む完全な JSON を管理します。Apple Gateway user skills は
他の user skill を巻き込まないよう、skill directory ごとに symlink します。

## AI agent user scopeとRiela

旧Home Managerが管理していたClaude user commands、Claude/Codex共通skills、
Cursor CLI設定、Peekaboo MCP設定は`agent-user-scope/`に固定しています。
bootstrapは既知のskill directoryだけを冪等に同期するため、Rielaや他の
インストーラーが管理するskillを削除しません。`envrc-generate`だけはdirenv廃止
方針により移植対象外です。

デスクトップではRiela caskの導入後、`agent-user-scope/riela-packages.txt`の
workflow/skill packageをuser scopeへインストールします。初回構築時に
`~/gits/tacogips/riela-packages`がなければ公開GitHub repositoryからcloneします。

GitHub HTTPS認証は`GITHUB_TOKEN` credential helperを使います。Fishには
`gh-token-export`、`gh-token-save-shared`、`gh-token-refresh`、`gh-token-reset`、
`gh-clone`を移植しています。commit/push前のcredential検査は、Claude/Codexの
`git-precommit-safety-check` user skillとして利用できます。

## 検証と Nix の削除

まず新しい shell で検証します。

```sh
mise -E macos-arm64 -E desktop run verify
```

問題がないことを確認してから、Nix を削除します。taskは最初にnix-darwinを
解除し、Determinate Installerがあればそのuninstallerを使います。それ以外は
公式のlegacy multi-user手順を安全確認付きで実行します。

```sh
mise run nix:uninstall -- --confirm
```

Nix の削除は不可逆です。taskはDeterminate Installerに加えて、公式Nixの
macOS legacy multi-user手順にも対応します。legacy経路ではAPFS `/nix` volume、
login shell、user-scopeのNix Store symlinkを事前検証し、変更するsystem fileを
`/var/backups/mise-darwin-nix-uninstall-*`へ退避してから削除します。実行内容だけを
確認する場合は次を使用します。

削除対象と順序は[Nix公式のmacOS multi-user uninstall手順](https://nix.dev/manual/nix/stable/installation/uninstall#macos)
に合わせています。

```sh
mise run nix:uninstall -- --confirm --dry-run
```

`tacogips/nix` は移行完了まで参照用に残し、このリポジトリの検証が通ってから
削除してください。

## 現時点の境界

- mise bootstrap は逐次収束で、nix-darwin の atomic switch / rollback はありません。
- Formula は mise の direct brew manager、Cask と API metadata のない third-party tap は Homebrew Bundle で収束します。既存 Homebrew cask の receipt と競合しないための分離です。
- Mac App Store は Apple Account、Xcode は初回起動・license 同意が必要な場合があります。
- system LaunchDaemon は必要になった時点で、確認可能な専用 task と plist を追加します。
- home server の `/etc` と volume directory は `home-server:apply` task が sudo で収束します。
