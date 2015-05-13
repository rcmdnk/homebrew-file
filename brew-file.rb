class BrewFile < Formula
  homepage 'https://github.com/rcmdnk/homebrew-file/'
  url 'https://github.com/rcmdnk/homebrew-file.git',
    :tag => "v3.4.1",
    :revision => "990c57bca908113b1727427d053608ee1eb5c9d5"
  head 'https://github.com/rcmdnk/homebrew-file.git', :branch => 'master'
  if build.include? "bash"
    url 'https://github.com/rcmdnk/homebrew-file.git', :branch => 'bash'
    version '1.1.8'
  end

  option "python", "Use python version (same as default)"
  option "bash", "Use bash version"

  skip_clean 'bin'

  def install
    prefix.install 'bin'
    (bin+'brew-file').chmod 0755
    prefix.install 'etc'
  end

  test do
    system "brew", "file", "help"
  end
end
