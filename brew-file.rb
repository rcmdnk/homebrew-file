require 'formula'

HOMEBREW_BREW_FILE_VERSION = '3.3.6'
HOMEBREW_BREW_FILE_BASH_VERSION = '1.1.8'
class BrewFile < Formula
  homepage 'https://github.com/rcmdnk/homebrew-file/'
  url 'https://github.com/rcmdnk/homebrew-file.git', :tag => "v#{HOMEBREW_BREW_FILE_VERSION}"
  version HOMEBREW_BREW_FILE_VERSION
  head 'https://github.com/rcmdnk/homebrew-file.git', :branch => 'master'
  if build.include? "bash"
    url 'https://github.com/rcmdnk/homebrew-file.git', :branch => 'bash'
    version HOMEBREW_BREW_FILE_BASH_VERSION
  end

  option "python", "Use python version (same as default)"
  option "bash", "Use bash version"

  skip_clean 'bin'

  def install
    prefix.install 'bin'
    (bin+'brew-file').chmod 0755
    prefix.install 'etc'
  end
end
