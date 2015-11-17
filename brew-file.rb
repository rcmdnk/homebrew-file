class BrewFile < Formula
  desc "Brewfile manager for Homebrew."
  homepage "https://github.com/rcmdnk/homebrew-file/"
<<<<<<< HEAD
  url "https://github.com/rcmdnk/homebrew-file/archive/v3.7.4.tar.gz"
  sha256 "ab57f696094243cd67f38fb164375748672adba56f32b1c20842341393a20680"
=======
  url "https://github.com/rcmdnk/homebrew-file/archive/v3.7.3.tar.gz"
  sha256 "0c1bee304b1d23ca59fdc81088b330056d9caad2dda1713d924e53f328dcdb10"
>>>>>>> 8bce7eedff9ae4d8c89729256299f9fac1cfef1c

  head "https://github.com/rcmdnk/homebrew-file.git"

  option "without-completions", "Disable bash/zsh completions"

  def install
    bin.install "bin/brew-file"
    (bin+"brew-file").chmod 0755
    etc.install "etc/brew-wrap"
    if build.with? "completions"
      bash_completion.install "etc/bash_completion.d/brew-file"
      zsh_completion.install "share/zsh/site-functions/_brew-file"
    end
  end

  test do
    system "brew", "file", "help"
  end
end
