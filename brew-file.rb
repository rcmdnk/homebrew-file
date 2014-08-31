require 'formula'

HOMEBREW_BREW_FILE_VERSION = '1.1.5'
class BrewFile < Formula
  homepage 'https://github.com/rcmdnk/homebrew-file/'
  url 'https://github.com/rcmdnk/homebrew-file.git', :tag => "v#{HOMEBREW_BREW_FILE_VERSION}"
  version HOMEBREW_BREW_FILE_VERSION
  head 'https://github.com/rcmdnk/homebrew-file.git', :branch => 'master'

  skip_clean 'bin'

  def install
    prefix.install 'bin'
    (bin+'brew-file').chmod 0755
  end
end
