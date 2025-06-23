
#
# .bashrc.override.sh
#

# persistent bash history
HISTFILE=~/.bash_history
PROMPT_COMMAND="history -a; $PROMPT_COMMAND"

# run entrypoint
source /entrypoint

# restore default shell options
set +o errexit
set +o pipefail
set +o nounset
