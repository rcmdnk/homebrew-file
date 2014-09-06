require 'formula'

HOMEBREW_BREW_FILE_VERSION = '1.1.7'
HOMEBREW_BREW_FILE_PYTHON_VERSION = '2.0.0'
class BrewFile < Formula
  homepage 'https://github.com/rcmdnk/homebrew-file/'
  url 'https://github.com/rcmdnk/homebrew-file.git', :tag => "v#{HOMEBREW_BREW_FILE_VERSION}"
  version HOMEBREW_BREW_FILE_VERSION
  head 'https://github.com/rcmdnk/homebrew-file.git', :branch => 'master'
  devel do
    url 'https://github.com/rcmdnk/homebrew-file.git', :branch => 'python'
    version HOMEBREW_BREW_FILE_PYTHON_VERSION
  end
  if build.include? "python"
    url 'https://github.com/rcmdnk/homebrew-file.git', :branch => 'python'
    version HOMEBREW_BREW_FILE_PYTHON_VERSION
  end

  option "python", "Use python version (same as devel)"

  skip_clean 'bin'

  def install
    prefix.install 'bin'
    (bin+'brew-file').chmod 0755
  end
end
