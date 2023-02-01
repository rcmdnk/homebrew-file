#!/usr/bin/env bash


dest="./bin/brew-file"
tmp_backup=$(mktemp -t brew-file)
mv "$dest" "$tmp_backup"
echo "Old brew-file was moved to $tmp_backup"

{
  echo "#!/usr/bin/env python3"
  grep -E "(^from|^import)" src/brew_file/*.py|grep -v "from \."| cut -d ":" -f2| sort -u
  grep -vE "(^from|^import)" < src/brew_file/info.py
  grep -vE "(^from|^import)" < src/brew_file/utils.py
  grep -vE "(^from|^import)" < src/brew_file/brew_helper.py
  grep -vE "(^from|^import)" < src/brew_file/brew_info.py
  grep -vE "(^from|^import)" < src/brew_file/brew_file.py
  grep -vE "(^from|^import)" < src/brew_file/main.py
} > "$dest"

black "$dest"
isort "$dest"
autoflake --in-place "$dest"
autopep8 --in-place "$dest"

diff -u "$tmp_backup" "$dest"
chmod 755 "$dest"
