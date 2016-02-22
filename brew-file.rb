class BrewFile < Formula
  desc "Brewfile manager for Homebrew."
  homepage "https://github.com/rcmdnk/homebrew-file/"
  url "https://github.com/rcmdnk/homebrew-file/archive/v3.10.7.tar.gz"
  sha256 "366e7ef5ea74466161965edc76a53dfbf8a9c15f095bb00a4e1482f6cd524428"

  head "https://github.com/rcmdnk/homebrew-file.git"

  option "without-completions", "Disable bash/zsh completions"

  def install
    bin.install "bin/brew-file"
    rm_f etc/"brew-wrap.default"
    rm_f etc/"brew-wrap"
    (prefix/"etc").install "etc/brew-wrap"
    if build.with? "completions"
      bash_completion.install "etc/bash_completion.d/brew-file"
      zsh_completion.install "share/zsh/site-functions/_brew-file"
    end
  end

  test do
    system "brew", "file", "help"
  end
end

