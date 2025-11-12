#!/bin/bash

CONTAINERS=(
  scorpio-iot-agent-1
  scorpio-scorpio-1
  scorpio-postgres-1
  db-mongo
)

PROJECT_ROOT="$(pwd)"
OUTPUT_FILE="$PROJECT_ROOT/twins_to_compare/scripts_for_measures/scorpio/measures/"$1-cpu_ram_sum"


#echo "Starting CPU/RAM monitoring for selected containers..."
echo "Timestamp, CPU%, MemUsageMiB, MemTotalMiB" > "$OUTPUT_FILE"

trap "echo 'Terminal closed, stopping monitoring.'; exit 0" SIGHUP SIGINT SIGTERM

while true; do

  for c in "${CONTAINERS[@]}"; do
    if ! docker ps -q -f name="^${c}$" | grep -q .; then
      echo "Le conteneur $c n'existe plus. Arrêt du script de mesure de CPU/RAM."
      exit 0
    fi
  done

  CPUP_SUM=0
  MEMUSAGE_SUM=0
  MEMTOTAL_SUM=0

  STATS_LIST=$(docker stats "${CONTAINERS[@]}" --no-stream --format "{{.CPUPerc}},{{.MemUsage}}")

while IFS=',' read -r CPU_PERC MEM_USAGE; do
  CPU_PERC=$(echo $CPU_PERC | tr -d '%' | tr ',' '.')
  MEM_USAGE_VALUE=$(echo $MEM_USAGE | awk '{print $1}' | tr ',' '.')
  MEM_USAGE_INT=$(echo "$MEM_USAGE_VALUE" | grep -oE '^[0-9]+')
  MEM_TOTAL_VALUE=$(echo $MEM_USAGE | awk '{print $3}' | tr ',' '.')
  MEM_TOTAL_INT=$(echo "$MEM_TOTAL_VALUE" | grep -oE '^[0-9]+')

  CPUP_SUM=$(echo "$CPUP_SUM + $CPU_PERC" | bc)
  MEMUSAGE_SUM=$(echo "$MEMUSAGE_SUM + $MEM_USAGE_INT" | bc)
  MEMTOTAL_SUM=$(echo "$MEMTOTAL_SUM + $MEM_TOTAL_INT" | bc)
done <<< "$STATS_LIST"

  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S.%3N")
  echo "$TIMESTAMP, $CPUP_SUM, $MEMUSAGE_SUM, $MEMTOTAL_SUM" >> "$OUTPUT_FILE"
done
