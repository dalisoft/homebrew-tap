class Lume < Formula
  desc "Run macOS/Linux VMs on Apple Silicon (CLI)"
  homepage "https://cua.ai"
  url "https://github.com/trycua/cua/releases/download/lume-v0.5.3/lume-0.5.3-darwin-arm64.tar.gz"
  version "0.5.3"
  sha256 "af5d0556763a7f0116153c220aaabe44974e775091ac57e38da2abb2959c63e8"
  license "MIT"

  # Upstream install.sh is macOS + ARM64 only, requires macOS 13+.
  livecheck do
    # Same as cua-driver: :git scans all tags (releases API is paged to 30
    # and lume tags sit past it; upstream also flags releases as prereleases).
    url :stable
    regex(/^lume-v?(\d+(?:\.\d+)+)$/i)
    strategy :git
  end

  depends_on arch: :arm64
  depends_on macos: :ventura

  def install
    # Tarball layout (verified read-only):
    #   lume               <- CLI wrapper
    #   lume.app/          <- bundled VM UI app (intentionally not installed to /Applications)
    # Install CLI only; app bundle stays out to avoid privileged moves and LaunchAgent side effects.
    bin.install "lume"
  end

  def caveats
    <<~EOS
      Apple Silicon only, macOS 13+ required.
      Upstream also ships lume.app and a LaunchAgent (`lume serve --port 7777`);
      this formula installs the `lume` CLI only.
      Start the daemon explicitly when needed:
        lume serve
      See: https://cua.ai/docs/how-to-guides/driver/install

      Full uninstall (formulae have no `zap` stanza — that is cask-only):
        brew uninstall --force lume
        # Only if you previously used upstream install.sh (this formula never creates these):
        # rm -rf ~/.local/share/lume ~/.local/bin/lume
        # launchctl unload ~/Library/LaunchAgents/com.trycua.lume_daemon.plist 2>/dev/null; rm -f ~/Library/LaunchAgents/com.trycua.lume_daemon.plist
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/lume --version")
  end
end
