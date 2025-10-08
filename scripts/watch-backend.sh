#!/bin/bash
# Auto-restart backend on file changes

WATCH_DIR="/root/panel/backend/app"
LOG_FILE="/tmp/backend-watcher.log"

echo "=== Backend File Watcher Started ===" | tee -a $LOG_FILE
echo "Watching: $WATCH_DIR" | tee -a $LOG_FILE

# Install inotify-tools if not present
if ! command -v inotifywait &> /dev/null; then
    echo "Installing inotify-tools..." | tee -a $LOG_FILE
    apt-get update -qq && apt-get install -y inotify-tools
fi

# Watch for changes
inotifywait -m -r -e modify,create,delete,move $WATCH_DIR --format '%T %w%f %e' --timefmt '%Y-%m-%d %H:%M:%S' |
while read timestamp file event; do
    # Ignore __pycache__ and .pyc files
    if [[ "$file" == *"__pycache__"* ]] || [[ "$file" == *".pyc" ]]; then
        continue
    fi
    
    echo "$timestamp - File changed: $file ($event)" | tee -a $LOG_FILE
    echo "Restarting backend..." | tee -a $LOG_FILE
    
    # Restart backend
    systemctl restart xray-panel-backend
    
    # Wait a bit before processing next change
    sleep 5
done
