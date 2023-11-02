max_retry_count=3
retry_interval=5

retry_count=0
while true; do
  docker compose up

  retry_count=$((retry_count + 1))
  if [ $retry_count -eq $max_retry_count ]; then
    echo "Error: command failed after $max_retry_count attempts"
    break
  fi

  echo "Command failed. Retrying in $retry_interval seconds..."
  sleep $retry_interval
done

