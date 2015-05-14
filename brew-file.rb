class BrewFile < Formula
  homepage 'https://github.com/rcmdnk/homebrew-file/'
  url 'https://github.com/rcmdnk/homebrew-file.git',
    :tag => "v3.4.3",
    :revision => "04c1772b3db483d2fe29ef2db105ccbb2a3f7eb9"
  head 'https://github.com/rcmdnk/homebrew-file.git', :branch => 'master'
  if build.include? "bash"
    url 'https://github.com/rcmdnk/homebrew-file.git', :branch => 'bash'
    version '1.1.8'
  end

  option "python", "Use python version (same as default)"
  option "bash", "Use bash version"
  option "without-completions", "Disable bash/zsh completions"

  skip_clean 'bin'

  def install
    bin.install 'bin/brew-file'
    (bin+'brew-file').chmod 0755
    etc.install 'etc/brew-wrap'
    share.install 'share'
  end

  if build.with? "completions"
    bash_completion.install "etc/bash_completion.d/brew-file"
    zsh_completion.install "share/zsh/site-functions/_brew-file"
  end

  test do
    system "brew", "file", "help"
  end
end
