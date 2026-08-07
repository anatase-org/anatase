#!/usr/bin/env bash

set -uo pipefail

channel="${1:-}"
version="${2:-}"
release_url="${3:-}"

warn() {
  echo "::warning::$1"
}

if [[ -z "${DISCORD_WEBHOOK_URL:-}" ]]; then
  warn "Discord release notification skipped: DISCORD_WEBHOOK_URL is not configured"
  exit 0
fi

if [[ -z "$channel" || -z "$version" || -z "$release_url" ]]; then
  warn "Discord release notification skipped: channel, version, and release URL are required"
  exit 0
fi

channel_title="${channel^}"
timestamp="$(date --utc +'%Y-%m-%dT%H:%M:%SZ')"
description="[View the full changelog and release details on GitHub]($release_url)"
role_id="${DISCORD_ROLE_ID:-}"

if ! payload="$(jq -nc \
    --arg title "Anatase $version — $channel_title Release" \
    --arg release_url "$release_url" \
    --arg description "$description" \
    --arg timestamp "$timestamp" \
    --arg role_id "$role_id" \
    '{
      allowed_mentions: {parse: []},
      embeds: [{
        title: $title,
        url: $release_url,
        description: $description,
        color: 16309515,
        timestamp: $timestamp
      }]
    }
    | if $role_id != "" then
        .content = "<@&\($role_id)>"
        | .allowed_mentions.roles = [$role_id]
      else
        .
      end'
  )"; then
  warn "Discord release notification skipped: could not generate the webhook payload"
  exit 0
fi

webhook_url="$DISCORD_WEBHOOK_URL"
if [[ "$webhook_url" == *\?* ]]; then
  webhook_url+="&wait=true"
else
  webhook_url+="?wait=true"
fi

if [[ -n "${DISCORD_THREAD_ID:-}" ]]; then
  webhook_url+="&thread_id=$DISCORD_THREAD_ID"
fi

if ! response="$(curl \
    --fail-with-body \
    --silent \
    --show-error \
    --retry 3 \
    --retry-connrefused \
    --retry-delay 2 \
    --retry-max-time 30 \
    --max-time 30 \
    --header 'Content-Type: application/json' \
    --data "$payload" \
    "$webhook_url" 2>&1
  )"; then
  warn "Discord release notification failed after retries: $response"
fi
