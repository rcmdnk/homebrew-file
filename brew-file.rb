class BrewFile < Formula
  desc "Brewfile manager for Homebrew."
  homepage "https://github.com/rcmdnk/homebrew-file/"
  url "https://github.com/rcmdnk/homebrew-file/archive/v8.1.0.tar.gz"
  sha256 "6ebcdbeb0ed7957ad823278e22d68e5801138ea35d8fcbf089bb2358469aa2f8"

  head "https://github.com/rcmdnk/homebrew-file.git"

  depends_on "python"

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
