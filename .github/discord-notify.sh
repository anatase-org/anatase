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
title="Anatase $version — $channel_title Release"
description="[View the release notes]($release_url)"
role_id="${DISCORD_ROLE_ID:-}"

if [[ "$release_url" == https://updates.anatase.org/* ]]; then
  if update_html="$(curl \
      --fail-with-body \
      --silent \
      --show-error \
      --location \
      --retry 3 \
      --retry-connrefused \
      --retry-delay 2 \
      --retry-max-time 30 \
      --max-time 30 \
      "$release_url" 2>/dev/null
    )" && summary="$(python3 .github/update-summary.py <<< "$update_html")"; then
    update_title="$(jq -r '.title // empty' <<< "$summary")"
    update_description="$(jq -r '.description // empty' <<< "$summary")"
    [[ -n "$update_title" ]] && title="$update_title"
    [[ -n "$update_description" ]] && description="$update_description"
  else
    warn "Could not read the update summary from $release_url; using fallback text"
  fi
fi

if ! payload="$(jq -nc \
    --arg title "$title" \
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
