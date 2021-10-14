#!/usr/bin/env fish
# brew command wrapper for brew-file

function brew
  set brew_exe (which brew)
  # Check if do wrap or not
  set wrap 1
  set v (python --version 2>&1|cut -d" " -f2|sed 's/\./\n/g')
  if test $v[1] -eq 2
    if test $v[2] -lt 7
      set wrap 0
    elif test $v[2] -eq 7 && test $v[3] -le 6
      set wrap 0
    end
  end

  # Set exe
  set exe "$brew_exe"

  # Do wrap
  if test $wrap -eq 1
    if test type -a brew-file
      # Check args
      set nargs (count $argv)
      set cmd $argv[1]
      set cmd2 $argv[2]

      # No auto update for tap listing
      set env ""
      if test "$cmd" = "tap" && test $nargs -eq 1
        set env "HOMEBREW_NO_AUTO_UPDATE=1"
      end

      switch $cmd
        # brew file
        case file
          set exe "brew-file"
        # brew install/uninstall/tap
        case install reinstall tap rm remove uninstall untap
          if [ $nargs -gt 1 ]
            set exe "brew-file brew"
          end
        # brew cask install/uninstall
        case cask
          if [ $nargs -gt 2 ]
            if [ "$cmd2" = "rm" ] || [ "$cmd2" = "remove" ] || \
                [ "$cmd2" = "uninstall" ] || [ "$cmd2" = "install" ] || \
                [ "$cmd2" = "instal" ]
              set exe "brew-file brew"
            end
          end
        case *
          if echo " brew init dump set_repo set_local pull push clean clean_non_request casklist get_files version "|grep -q -- " $argv[1] "
            set exe "brew-file"
          end
      end
    end
  end

  eval $env $exe $argv
  return $status
end
