#!/bin/bash
# sync-upstream.sh — Sync channel implementations from upstream tools
#
# Usage: ./scripts/sync-upstream.sh
#
# This script checks for updates in x-reader's fetchers/ directory
# and shows which files have changed. You can then manually review
# and merge the changes.

set -e

UPSTREAM_REPO="runesleo/x-reader"
UPSTREAM_BRANCH="main"
UPSTREAM_DIR="x_reader/fetchers"
LOCAL_DIR="agent_reach/channels"

echo "👁️ Agent Reach — Upstream Sync"
echo "Checking for updates from $UPSTREAM_REPO..."
echo ""

# Create temp dir for upstream code
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Clone upstream (shallow)
git clone --depth 1 --branch "$UPSTREAM_BRANCH" \
    "https://github.com/$UPSTREAM_REPO.git" "$TMPDIR/upstream" 2>/dev/null

if [ ! -d "$TMPDIR/upstream/$UPSTREAM_DIR" ]; then
    echo "❌ Upstream directory not found: $UPSTREAM_DIR"
    echo "   x-reader may have changed their structure."
    exit 1
fi

# Compare each file
echo "Comparing files..."
echo ""

CHANGES=0
for upstream_file in "$TMPDIR/upstream/$UPSTREAM_DIR"/*.py; do
    filename=$(basename "$upstream_file")
    local_file="$LOCAL_DIR/$filename"
    
    if [ ! -f "$local_file" ]; then
        echo "🆕 NEW: $filename (exists in upstream but not locally)"
        CHANGES=$((CHANGES + 1))
        continue
    fi
    
    # Compare (ignoring import path differences)
    if ! diff -q <(sed 's/x_reader\.fetchers/agent_reach.channels/g' "$upstream_file") "$local_file" > /dev/null 2>&1; then
        echo "📝 CHANGED: $filename"
        diff --color -u <(sed 's/x_reader\.fetchers/agent_reach.channels/g' "$upstream_file") "$local_file" | head -20
        echo "   ..."
        echo ""
        CHANGES=$((CHANGES + 1))
    fi
done

if [ $CHANGES -eq 0 ]; then
    echo "✅ All channels are up to date with upstream!"
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$CHANGES file(s) have upstream changes."
    echo ""
    echo "To merge a specific file:"
    echo "  cp $TMPDIR/upstream/$UPSTREAM_DIR/FILENAME.py $LOCAL_DIR/FILENAME.py"
    echo "  sed -i 's/x_reader\\.fetchers/agent_reach.channels/g' $LOCAL_DIR/FILENAME.py"
    echo ""
    echo "Then review changes, run tests, and commit."
fi
