class CuaDriver < Formula
  desc "Open-source computer-use driver (CLI)"
  homepage "https://cua.ai"
  version "0.28.2"
  license "MIT"

  livecheck do
    url :stable
    regex(/^cua-driver-rs-v?(\d+(?:\.\d+)+)$/i)
    strategy :github_latest
  end

  on_macos do
    on_arm do
      url "https://github.com/trycua/cua/releases/download/cua-driver-rs-v0.28.2/cua-driver-rs-0.28.2-darwin-arm64.tar.gz"
      sha256 "818ddefa0fa8ba2ec9cba837c7aa634a4b064221c748752cf49c5b08e2c94e8c"
    end
    on_intel do
      url "https://github.com/trycua/cua/releases/download/cua-driver-rs-v0.28.2/cua-driver-rs-0.28.2-darwin-x86_64.tar.gz"
      sha256 "9e00cc92480a8f3d32bbcb7cb45cbc42293b7bd13c1808f5047f1f73a8b64f24"
    end
    # Upstream docs: macOS 14+ required.
    depends_on macos: :sonoma
  end

  on_linux do
    on_arm do
      url "https://github.com/trycua/cua/releases/download/cua-driver-rs-v0.28.2/cua-driver-rs-0.28.2-linux-arm64.tar.gz"
      sha256 "cadd7e6b757c3ce50f2b5f6e273c154ea48450fb5fcaff744209b382915eddf5"
    end
    on_intel do
      url "https://github.com/trycua/cua/releases/download/cua-driver-rs-v0.28.2/cua-driver-rs-0.28.2-linux-x86_64.tar.gz"
      sha256 "8f3e5b669e2bcd98d0eecc64f40640aac77f358b6332a06abc6ee79991620f7d"
    end
    # Prebuilt Rust binary; gcc provides runtime linker on Linux.
    depends_on "gcc"
  end

  def install
    # Tarball layout (verified read-only, never executed):
    #   cua-driver-rs-<version>-<target>/cua-driver
    #   cua-driver-rs-<version>-<target>/cua-cursor-theme
    #   [+ CuaDriver.app on macOS, wayland-helper on Linux — intentionally not installed]
    # Install CLI binaries only to keep formula side-effect free (no /Applications writes,
    # no LaunchAgents, no PATH rc edits performed by upstream install.sh).
    bin.install Dir["cua-driver-rs-*/cua-driver"].first => "cua-driver"
    bin.install Dir["cua-driver-rs-*/cua-cursor-theme"].first => "cua-cursor-theme"
  end

  def caveats
    <<~EOS
      This formula installs the CLI binaries only (`cua-driver`, `cua-cursor-theme`).
      Upstream install.sh also installs /Applications/CuaDriver.app (macOS TCC),
      LaunchAgents/Scheduled Tasks and PATH edits — none of that is done here.
      Linux requires X11/XWayland plus system libs (e.g. `libxi6`, `at-spi2-core`);
      Wayland support is opt-in via CUA_DRIVER_RS_ENABLE_WAYLAND=1.
      See: https://cua.ai/docs/how-to-guides/driver/install

      Full uninstall (formulae have no `zap` stanza — that is cask-only):
        brew uninstall --force cua-driver
        # Only if you previously used upstream install.sh (this formula never creates these):
        # rm -rf ~/.cua-driver
        # rm -rf /Applications/CuaDriver.app
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/cua-driver --version")
  end
end
