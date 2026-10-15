#!/usr/bin/env bash
# Build an argv array for Linux without flattening application values.
make_linux_args() {
  LINUX_ARGS=("--operator=$OPERATOR" "--optional=$OPTIONAL" "--concurrent=$CONCURRENT" "--timeout=$TIMEOUT")
  [[ ${SKIP_SYSTEM:-false} != true ]] || LINUX_ARGS+=(--skip-system)
  if [[ ${#ONLY_APPS[@]} -gt 0 ]]; then
    local joined
    joined=$(IFS=,; printf '%s' "${ONLY_APPS[*]}")
    LINUX_ARGS+=("--only=$joined")
  fi
  local app
  for app in ${ENABLE_APPS[@]+"${ENABLE_APPS[@]}"}; do LINUX_ARGS+=("--enable-$app"); done
  for app in ${DISABLE_APPS[@]+"${DISABLE_APPS[@]}"}; do LINUX_ARGS+=("--disable-$app"); done
  for app in ${APP_FLAG_ARGS[@]+"${APP_FLAG_ARGS[@]}"}; do LINUX_ARGS+=("--app_flag=$app"); done
}
