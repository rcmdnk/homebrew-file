require 'formula'

HOMEBREW_BREWALL_VERSION = '0.1.0'
class Brewall < Formula
  homepage 'https://github.com/rcmdnk/homebrew-brewall/'
  url 'https://github.com/rcmdnk/homebrew-brewall.git', :tag => "v#{HOMEBREW_BREWALL_VERSION}"
  version HOMEBREW_BREWALL_VERSION
  head 'https://github.com/rcmdnk/homebrew-brewall.git', :branch => 'master'

  skip_clean 'bin'

  def install
    prefix.install 'bin'
    (bin+'brewall').chmod 0755
  end
end
