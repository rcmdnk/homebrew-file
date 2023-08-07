class BrewFile < Formula
  desc "Brewfile manager for Homebrew."
  homepage "https://github.com/rcmdnk/homebrew-file/"
  url "https://github.com/rcmdnk/homebrew-file/archive/v9.0.14.tar.gz"
  sha256 "4b04be9dad580f731e353ec47e0c72683eea05899299cc25730de1d28594febc"
  license "MIT"

  head "https://github.com/rcmdnk/homebrew-file.git"

  option "without-completions", "Disable bash/zsh completions"

  def install
    bin.install "bin/brew-file"
    rm_f etc/"brew-wrap.default"
    rm_f etc/"brew-wrap"
    rm_f etc/"brew-wrap.fish"
    (prefix/"etc").install "etc/brew-wrap"
    (prefix/"etc").install "etc/brew-wrap.fish"
    if build.with? "completions"
      bash_completion.install "etc/bash_completion.d/brew-file"
      zsh_completion.install "share/zsh/site-functions/_brew-file"
    end
  end

  test do
    system "brew", "file", "help"
  end
end
