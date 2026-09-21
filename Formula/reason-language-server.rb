class ReasonLanguageServer < Formula
  desc "Language Server Protocol implementation for Reason"
  homepage "https://github.com/jaredly/reason-language-server"
  version "1.7.13"
  license "MIT"

  livecheck do
    url :stable
    regex(/^v?(\d+(?:\.\d+)+)$/i)
    strategy :github_latest
  end

  on_macos do
    # x86_64-era binary (runs via Rosetta 2 on ARM); same asset for both archs.
    on_arm do
      url "https://github.com/jaredly/reason-language-server/releases/download/1.7.13/rls-macos.zip"
      sha256 "e51583016585980a7aee5c7680f5f70d5844b2436073235fba0c03ea59b0f88c"
    end
    on_intel do
      url "https://github.com/jaredly/reason-language-server/releases/download/1.7.13/rls-macos.zip"
      sha256 "e51583016585980a7aee5c7680f5f70d5844b2436073235fba0c03ea59b0f88c"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/jaredly/reason-language-server/releases/download/1.7.13/rls-linux.zip"
      sha256 "b5960cf3a23e866da1735c0f46cf10b6f2a1fe4674a0d481c52542ca2c68ddbc"
    end
    on_intel do
      url "https://github.com/jaredly/reason-language-server/releases/download/1.7.13/rls-linux.zip"
      sha256 "b5960cf3a23e866da1735c0f46cf10b6f2a1fe4674a0d481c52542ca2c68ddbc"
    end
  end

  def install
    # Zip layout (verified read-only via `unzip -l`, never executed):
    #   rls-macos/reason-language-server  (macOS)
    #   rls-linux/reason-language-server  (Linux)
    # Single CLI binary; install under stable name on both OSes.
    bin.install Dir["rls-*/reason-language-server"].first => "reason-language-server"
  end

  def caveats
    <<~EOS
      Upstream is deprecated/unmaintained since the `rescript` split (last release 2020-10-07).
      Consider `rescript-vscode` or `ocaml/ocaml-lsp` for new projects.
      This is an x86_64-era binary; on Apple Silicon it runs via Rosetta 2.
      macOS Gatekeeper may quarantine the binary on first run; remove quarantine only
      after verifying the SHA-256 above against the GitHub release page.

      Full uninstall (formulae have no `zap` stanza — that is cask-only):
        brew uninstall --force reason-language-server
        # No user data is created by this binary (editor configs live in your editor settings).
    EOS
  end

  test do
    # LSP server blocks on stdin; do not invoke it. Verify install correctness only.
    assert_path_exists bin/"reason-language-server"
    assert_predicate bin/"reason-language-server", :executable?
  end
end
