class BrewFile < Formula
  desc "Brewfile manager for Homebrew."
  homepage "https://github.com/rcmdnk/homebrew-file/"
  url "https://github.com/rcmdnk/homebrew-file"

  def install
  end

  def caveats
    <<-EOS.undent
      Homebrew-file is installed by `brew tap rcmdnk/homebrew-file`.
      and is updated by `brew update`.
      `brew install` is no longer needed.
    EOS
  end

  test do
    system "brew", "file", "help"
  end
end

