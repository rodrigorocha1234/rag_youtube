#!/bin/bash

set -e

rm -rf ./pgdata/ ./storage-data/

mkdir -p ./pgdata/ ./storage-data/

chmod -R 777 ./pgdata/ ./storage-data/