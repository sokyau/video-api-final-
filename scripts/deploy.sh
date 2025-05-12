#!/bin/bash
echo "Desplegando aplicación..."
docker-compose down
docker-compose build
docker-compose up -d
echo "Despliegue completado"
