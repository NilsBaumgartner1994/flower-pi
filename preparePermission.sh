#!/bin/bash
echo "Setting read/write permission for uploads"
mkdir -p ./data/database_file_uploads/
chmod -R 777 ./data/database_file_uploads/

echo "Setting read/write permission for database"
# Ensure the database directory exists
mkdir -p ./data/database/
# Set read/write/execute permissions for all users
chmod -R 777 ./data/database/

echo "Setting read/write permission for database backups"
# Ensure the database backups directory exists
mkdir -p ./data/database_backups/
# Set read/write/execute permissions for all users
chmod -R 777 ./data/database_backups/

echo "Setting read/write permission for .env file"
# Set read/write permissions for all users on the .env file
chmod 666 .env

echo "Finished"
