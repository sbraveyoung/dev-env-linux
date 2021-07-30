# .bash_profile

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

# User specific environment and startup programs

# export PS1="\u@\h \W \[\033[31m\][\$(echo_sentence)]\[\033[00m\] \[\033[33m\][\$(echo_date)]\[\033[00m\]\[\033[32m\]\$(parse_git_branch)\[\033[00m\] $"
export PS1="\u@\h \W \[\033[33m\][\$(echo_date)]\[\033[00m\]\[\033[32m\]\$(parse_git_branch)\[\033[00m\] $"

export PATH="$HOME/.cargo/bin:$PATH"
