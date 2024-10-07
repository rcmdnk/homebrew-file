class BrewFile < Formula
  desc "Brewfile manager for Homebrew."
  homepage "https://github.com/rcmdnk/homebrew-file/"
  url "https://github.com/rcmdnk/homebrew-file/archive/v9.1.3.tar.gz"
  sha256 "4e2e682d7c4a955fed7dbe0f559cdb163df8e1e881fe6870b03140200f133736"
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
