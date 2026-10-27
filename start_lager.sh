#!/usr/bin/env bash
# Starts LAGER in Docker and opens it in the browser (Linux and macOS).
# Requirement: Docker is installed and running.

IMAGE="lager"
PORT=5000

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running (or you have no permission to use it)."
    echo "Please start Docker and try again."
    read -rp "Press Enter to close."
    exit 1
fi

# Remove a LAGER container left over from an earlier session
docker rm -f lager >/dev/null 2>&1

echo "Starting LAGER..."
if ! docker run -d --rm --name lager -p "127.0.0.1:${PORT}:5000" "$IMAGE" >/dev/null; then
    echo "LAGER could not be started. Is the image \"$IMAGE\" available?"
    read -rp "Press Enter to close."
    exit 1
fi

# Wait until the page answers (at most ~30 s)
for _ in $(seq 30); do
    curl -s "http://localhost:${PORT}" >/dev/null 2>&1 && break
    sleep 1
done

URL="http://localhost:${PORT}"
(xdg-open "$URL" || open "$URL") >/dev/null 2>&1 &

echo
echo "LAGER is running at $URL"
echo "Keep this window open while you work."
read -rp "Press Enter to stop LAGER."
docker stop lager >/dev/null
