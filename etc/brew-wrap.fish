# brew command wrapper for brew-file
function brew
  # Set exe
  set -l exe command brew

  if not type -q brew-file
    $exe $argv
    return
  end

  # Do wrap
  # Check args
  set -l nargs 0
  for a in $argv
    if string match -qv '^-' -- $a
      set nargs (math $nargs + 1)
    end
  end
  set -l cmd $argv[1]
  set -l cmd2 $argv[2]

  # No auto update for tap listing
  set -l env ""
  if test "$cmd" = "tap" -a $nargs -eq 1
    set env "HOMEBREW_NO_AUTO_UPDATE=1"
  end

  switch "$cmd"
    case 'file'
      set exe brew-file
      set argv $argv[2..-1]
    case 'install' 'reinstall' 'tap' 'rm' 'remove' 'uninstall' 'untap'
      if test $nargs -gt 1
        set exe brew-file brew
      end
    case 'cask'
      if test $nargs -gt 2
        switch "$cmd2"
          case 'rm' 'remove' 'uninstall' 'install' 'instal'
            set exe brew-file brew
        end
      end
    case '*'
      if echo " brew init dump set_repo set_local pull push clean clean_non_request casklist get_files version "| grep -q " $cmd "
        set exe brew-file
      end
  end

  # Remove noinit option for pure brew command
  if test "$exe" = "command brew" -a "$argv[1]" = "noinit"
    set argv $argv[2..-1]
  end

  # Execute command
  set -l brewfile (brew-file cat 2>/dev/null)
  eval "$env $exe $argv"
  set -l ret $status

  # Commands after brew command
  set -l brewfile_after (brew-file cat 2>/dev/null)
  if test $ret -eq 0
    if not diff (echo $brewfile | psub) (echo $brewfile_after | psub) >/dev/null
      _post_brewfile_update
    end
  end

  return $ret
end

function _post_brewfile_update
  # Empty function placeholder
end

# mas command wrapper for brew-file
function mas
  # Set exe
  set -l exe command mas

  if type -q brew-file
    # Check args
    set -l cmd $argv[1]

    switch "$cmd"
      case 'purchase' 'install' 'uninstall'
        set exe brew-file brew mas
    end
  end

  # Execute command
  $exe $argv
end

# whalebrew command wrapper for brew-file
function whalebrew
  # Set exe
  set -l exe command whalebrew

  if type -q brew-file
    # Check args
    set -l cmd $argv[1]

    switch "$cmd"
      case 'install' 'uninstall'
        set exe brew-file brew whalebrew
    end
  end

  # Execute command
  $exe $argv
end

# code (for VSCode) command wrapper for brew-file
function code
  # Set exe
  set -l exe command code

  if type -q brew-file
    # Check args
    set -l cmd $argv[1]

    switch "$cmd"
      case '--install-extension' '--uninstall-extension'
        set exe brew-file brew code
    end
  end

  # Execute command
  $exe $argv
end
