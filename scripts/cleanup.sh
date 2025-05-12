#!/bin/bash
echo "Limpiando archivos temporales..."
find ./temp -type f -mtime +1 -delete
find ./logs -name "*.log" -mtime +7 -delete
echo "Limpieza completada"
