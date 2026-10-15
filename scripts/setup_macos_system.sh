#!/usr/bin/env bash

set -euo pipefail

# Keep default user prefixes owned by the current user; never make them world-writable.
for directory in "${GOPATH}" "${CLONE_PATH}" "${APP_PATH}" "${BIN_PATH}"; do
  case "$directory" in
    "$HOME"/*)
      mkdir -p "$directory"
      if [[ ! -w "$directory" ]]; then
        sudo chown "$(id -u):$(id -g)" "$directory"
      fi
      ;;
    *) sudo mkdir -p "$directory" ;;
  esac
done

# 触摸板轻点,不用重按
defaults write com.apple.AppleMultitouchTrackpad Clicking -int 1
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# 三指拖拽
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadThreeFingerDrag -bool true
defaults write com.apple.AppleMultitouchTrackpad TrackpadThreeFingerDrag -bool true

# 自动隐藏 dock
defaults write com.apple.dock autohide -bool true
