class CommandCode < Formula
  desc "Coding agent that learns your coding taste (CLI)"
  homepage "https://commandcode.ai"
  url "https://registry.npmjs.org/command-code/-/command-code-1.58.1.tgz"
  sha256 "c00c1155f9b118d8ad5c516c2afa554280b96a9b68c5f03d529267409012e1f8"
  # Upstream npm license field is UNLICENSED (proprietary).
  # Homebrew SPDX vocabulary has no value for that, so mark as non-representable.
  license :cannot_represent

  # Upstream engines: { node: ">=22" }. Use current Homebrew node (satisfies >=22).
  livecheck do
    # :stable is the npm registry tarball; :npm parses the package name from it.
    url :stable
    strategy :npm
  end

  depends_on "node"

  on_macos do
    # Node 22+ requires a modern macOS; require Monterey or newer.
    depends_on macos: :monterey
  end

  def install
    # Standard npm install into libexec (isolated, no global npm pollution).
    # Follows https://docs.brew.sh/Language-Specific-Formulae#standard-npm-installation
    system "npm", "install", *std_npm_args
    # Upstream bins: cmd, cmdc, commandcode, command-code -> dist/index.mjs
    bin.install_symlink libexec.glob("bin/*")
  end

  def caveats
    <<~EOS
      Requires Node.js >= 22 (provided via Homebrew dependency).
      Upstream binaries: `command-code`, `commandcode`, `cmd` (macOS/Linux), `cmdc` (Windows name).
      First run requires login:
        command-code login
      Docs: https://commandcode.ai/docs/quickstart

      Full uninstall (formulae have no `zap` stanza — that is cask-only):
        brew uninstall --force command-code
        rm -rf ~/.commandcode   # auth.json, login session, user data (only if you want it gone)
    EOS
  end

  test do
    # Basic functionality: version output contains packaged version.
    assert_match version.to_s, shell_output("#{bin}/command-code --version")
  end
end
