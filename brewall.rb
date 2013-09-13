require 'formula'

class Brewall < Formula
  homepage 'https://github.com/rcmdnk/brewall/'
  url 'https://github.com/rcmdnk/brewall.git'

  head 'https://github.com/rcmdnk/brewall.git', :branch => 'master'

  skip_clean 'bin'

  def install
    prefix.install 'bin'
    (bin+'brewall').chmod 0755
  end
end
