#!/usr/bin/env bash


output=./bin/brew-file
{
  echo "#!/usr/bin/env python3"
  grep -E "(^from|^import)" src/brew_file/*.py|grep -v "from \."| cut -d ":" -f2|sort -u
  grep -vE "(^from|^import)" < src/brew_file/info.py
  grep -vE "(^from|^import)" < src/brew_file/utils.py
  grep -vE "(^from|^import)" < src/brew_file/brew_helper.py
  grep -vE "(^from|^import)" < src/brew_file/brew_info.py
  grep -vE "(^from|^import)" < src/brew_file/brew_file.py
  grep -vE "(^from|^import)" < src/brew_file/main.py
} > $output

black $output
isort $output
autoflake --in-place $output
autopep8 --in-place $output
