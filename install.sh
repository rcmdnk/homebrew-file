#!/bin/bash
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

  if echo $OSTYPE | grep -q darwin;then
    arc=$(uname -m)
    if [ "$arc" = "x86_64" ];then
      paths=(/usr/local /opt/homebrew)
    else
      paths=(/opt/homebrew /usr/local)
    fi
  else
    paths=(/home/linuxbrew/.linuxbrew "$HOME/.linuxbrew" /opt/homebrew /usr/local)
  fi

  for path in "${paths[@]}";do
    if [ -f "$path/bin/brew" ];then
      export PATH="$path/sbin:$path/bin:$PATH"
      break
    fi
  done
fi

echo
echo Install Brew-file...

brew install rcmdnk/file/brew-file

if [ $brew_installed -eq 0 ];then
  # Do not check stray files
  if ! brew doctor $(brew doctor --list-checks | grep -vE '(dylibs|static_libs|headers|cask|brew_git_branch)');then
    echo Check brew environment!
    exit 1
  fi
fi
