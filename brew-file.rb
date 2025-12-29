class BrewFile < Formula
  desc "Brewfile manager for Homebrew."
  homepage "https://github.com/rcmdnk/homebrew-file/"
  url "https://github.com/rcmdnk/homebrew-file/archive/v10.1.4.tar.gz"
  sha256 "f29b9c2fe02eb721ec1bce3347d002a74f6363b1ca7ed7d336cadb5986369942"
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
