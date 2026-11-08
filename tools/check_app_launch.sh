#!/usr/bin/env bash
# Launch a SwiftPM macOS app executable and verify it behaves like a real app:
# macOS registers it as a Foreground application and it owns at least one on-screen window.
# Works without screen-recording permission (uses lsappinfo + CGWindowList owner info only).
#
#   tools/check_app_launch.sh App/HelloMac HelloMac
set -euo pipefail

package_dir="$1"
product="$2"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

swift build --package-path "$root/$package_dir" --product "$product" >/dev/null
binary="$(swift build --package-path "$root/$package_dir" --show-bin-path)/$product"

"$binary" >/dev/null 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true' EXIT

app_type="" windows=0
for _ in $(seq 1 20); do
    sleep 0.5
    app_type="$(lsappinfo info -only ApplicationType "$(lsappinfo find pid="$pid")" 2>/dev/null |
        sed -n 's/.*"ApplicationType"="\([^"]*\)".*/\1/p')"
    windows="$(swift -e "
import CoreGraphics
let list = CGWindowListCopyWindowInfo([.optionOnScreenOnly], kCGNullWindowID) as? [[String: Any]] ?? []
print(list.filter { (\$0[kCGWindowOwnerPID as String] as? Int32) == $pid && (\$0[kCGWindowLayer as String] as? Int) == 0 }.count)
" 2>/dev/null || echo 0)"
    [[ "$app_type" == "Foreground" && "$windows" -gt 0 ]] && break
done

echo "$product: ApplicationType=${app_type:-unknown}, on-screen windows=$windows"
if [[ "$app_type" != "Foreground" || "$windows" -eq 0 ]]; then
    echo "FAILED: $product did not launch as a foreground app with a window" >&2
    exit 1
fi
echo "OK"
