#!/usr/bin/env bash
# Keep this repository's Rust SDK separate from existing user Rust installations.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/catalog.sh"
catalog_load defaults --platform linux
rust_sdk_command() {
  RUSTUP_HOME="$APP_PATH/rust-sdk/rustup" CARGO_HOME="$APP_PATH/rust-sdk/cargo" \
    "$APP_PATH/rust-sdk/cargo/bin/$1" "${@:2}"
}
rust_sdk_activate() {
  local tool link wrapper
  mkdir -p "$APP_PATH/rust-sdk/bin" "$BIN_PATH"
  for tool in cargo rustc rustdoc rustup; do
    link="$BIN_PATH/$tool"
    wrapper="$APP_PATH/rust-sdk/bin/$tool"
    if [[ -e "$link" || -L "$link" ]]; then
      [[ -L "$link" && $(readlink "$link") == "$wrapper" ]] || {
        printf 'refusing to replace unmanaged Rust command: %s\n' "$link" >&2; return 1;
      }
    fi
  done
  for tool in cargo rustc rustdoc rustup; do
    wrapper="$APP_PATH/rust-sdk/bin/$tool"
    {
      printf '%s\n' '#!/usr/bin/env bash'
      printf 'exec env RUSTUP_HOME=%q CARGO_HOME=%q %q "$@"\n' \
        "$APP_PATH/rust-sdk/rustup" "$APP_PATH/rust-sdk/cargo" "$APP_PATH/rust-sdk/cargo/bin/$tool"
    } > "$wrapper"
    chmod +x "$wrapper"
    ln -sfn "$wrapper" "$BIN_PATH/$tool"
  done
}
install_linux_rust() {
  local target url executable
  target=$(catalog_field rust "targets.$(linux_arch)") || return
  url=$(catalog_field rust download_url --target "$target") || return
  executable="${CLONE_PATH}/rustup-init-${target}"
  wget_nx "$url" -O "$executable"
  python3 "${REPO_ROOT}/scripts/verified_download.py" rustup "$executable" "$url" "$target"
  chmod +x "$executable"
  RUSTUP_HOME="$APP_PATH/rust-sdk/rustup" CARGO_HOME="$APP_PATH/rust-sdk/cargo" \
    "$executable" -y --profile minimal --no-modify-path --default-toolchain "$RUST_VERSION"
  rust_sdk_activate
  printf '%s\n' "$RUST_VERSION" > "$APP_PATH/rust-sdk/version"
}
upgrade_linux_rust() {
  local previous
  previous=$(rust_sdk_command rustc --version | awk '{print $2}') || return
  rust_sdk_command rustup update stable || return
  rust_sdk_command rustup default stable || return
  printf '%s\n' "$previous" > "$APP_PATH/rust-sdk/previous-version"
  rust_sdk_activate
}
rollback_linux_rust() {
  local previous
  previous=$(cat "$APP_PATH/rust-sdk/previous-version") || return
  rust_sdk_command rustup default "$previous" || return
  rust_sdk_activate
}
uninstall_linux_rust() {
  local tool
  for tool in cargo rustc rustdoc rustup; do
    if [[ -L "$BIN_PATH/$tool" && $(readlink "$BIN_PATH/$tool") == "$APP_PATH/rust-sdk/bin/$tool" ]]; then
      rm -- "$BIN_PATH/$tool"
    fi
  done
  # Retain this private SDK; never delete ~/.cargo or ~/.rustup owned by the user.
}
