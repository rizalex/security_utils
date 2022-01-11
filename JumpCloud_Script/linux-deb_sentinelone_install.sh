# Plase run this script using root, modify the file name and keep the token secure secret.
sudo dpkg -i /tmp/SentinelAgent_linux_v21.deb
sudo /opt/sentinelone/bin/sentinelctl management token set eyJ1cmwiOiAiaHR0cHM6Ly91c2VhMS0wMDEtbXNzcC5zZW50aW5lbG9uZS5uZXQiLCAic2l0ZV9rZXkiOiAiOTkyNDJmMWZmNWFiZjQ2MSJ9
sudo /opt/sentinelone/bin/sentinelctl control start
