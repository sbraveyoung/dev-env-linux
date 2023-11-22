#!/usr/bin/env bash

set -exuo pipefail

# 触摸板轻点,不用重按
defaults write com.apple.AppleMultitouchTrackpad Clicking -int 1
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# 三指拖拽
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadThreeFingerDrag -bool true
defaults write com.apple.AppleMultitouchTrackpad TrackpadThreeFingerDrag -bool true

# 关闭第三方程序验证
sudo spctl --master-disable
defaults write com.apple.LaunchServices LSQuarantine -bool false

# 关闭 dmg 镜像验证
defaults write com.apple.frameworks.diskimages skip-verify -bool true
defaults write com.apple.frameworks.diskimages skip-verify-locked -bool true
defaults write com.apple.frameworks.diskimages skip-verify-remote -bool true

# 自动隐藏 dock
defaults write com.apple.dock autohide -bool true
