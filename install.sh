#!/bin/sh
brew_installed=1
if ! which brew > /dev/null 2>&1;then
  brew_installed=0
  echo Homebrew is not installed!
  echo Install now...
  echo /bin/bash -c \"\$\(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh\)\"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ret=$?
  if [ $ret -ne 0 ];then
    echo Failed to install Homebrew... please check your environment
    exit $ret
  fi
  echo

  for path in /home/linuxbrew/.linuxbrew $HOME/.linuxbrew /opt/homebrew /usr/local;do
    if [ -f "$path/bin" ];then
      PATH="$path/bin/brew"
    fi
  done
fi

echo
echo Install Brew-file...

brew install rcmdnk/file/brew-file

if [ $brew_installed -eq 0 ];then
  brew doctor
  if [ $? -ne 0 ];then
    echo Check brew environment!
    exit 1
  fi
fi
