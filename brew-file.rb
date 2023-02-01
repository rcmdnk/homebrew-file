class BrewFile < Formula
  desc "Brewfile manager for Homebrew."
  homepage "https://github.com/rcmdnk/homebrew-file/"
  url "https://github.com/rcmdnk/homebrew-file/archive/v8.5.12.tar.gz"
  sha256 "839d92a863def1ed393b60fc2947cec3839e17a8655219a53efa49f731e0b9dd"

  head "https://github.com/rcmdnk/homebrew-file.git"

  depends_on "python@3.10"

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
