#!/bin/bash
# Compile the Swift/AVFoundation media tools once into a cache dir and print that dir.
# Usage: BIN=$(bash build.sh)   then   "$BIN/dense" video.mp4 outdir 0.04 320
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
BIN="${VIDEO_TOOLS_BIN:-$HOME/Library/Caches/video-tools-macos/bin}"
mkdir -p "$BIN"
for f in "$SRC"/*.swift; do
  name="$(basename "$f" .swift)"
  if [ ! -x "$BIN/$name" ] || [ "$f" -nt "$BIN/$name" ]; then
    swiftc -O -suppress-warnings "$f" -o "$BIN/$name" >&2
  fi
done
echo "$BIN"
