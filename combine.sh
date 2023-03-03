#!/usr/bin/env bash

src="./src/brew_file"
dest="./bin/brew-file"

black "$src"
autoflake --in-place "$src/"*.py
autopep8 --in-place "$src/"*.py
isort "$src"

tmp_backup=$(mktemp)
if [ -f "$dest" ];then
  mv "$dest" "$tmp_backup"
  echo "Old brew-file was moved to $tmp_backup"
fi

imports=""
contents=""

for f in "$src/"{info.py,utils.py,brew_helper.py,brew_info.py,brew_file.py,main.py}; do
  import_flag=0
  while IFS= read -r line;do
    if [ "$import_flag" -gt 0 ]; then
      if [ "$import_flag" -eq 1 ]; then
        imports="$imports$line"$'\n'
      fi
      if [[ "$line" =~ \) ]];then
        import_flag=0
      fi
    elif [[ "$line" =~ (^from|^import) ]];then
      if [[ ! "$line" =~ from\ *\. ]];then
        imports="$imports$line"$'\n'
      fi
      if [[ "$line" =~ \( ]] && [[ ! "$line" =~ \) ]];then
        if [[ "$line" =~ from\ *\. ]];then
          import_flag=2
        else
          import_flag=1
        fi
      fi
    else
      contents="$contents$line"$'\n'
    fi
  done < "$f"
done

{
  echo "#!/usr/bin/env python3"
  echo "$imports"
  echo "$contents"
} > "$dest"

black "$dest"
autoflake --in-place "$dest"
autopep8 --in-place "$dest"
isort "$dest"

if [ -f "$tmp_backup" ];then
  diff -u "$tmp_backup" "$dest"
fi
chmod 755 "$dest"
